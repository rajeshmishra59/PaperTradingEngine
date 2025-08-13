# main_papertrader_optimized.py
# OPTIMIZED VERSION: Parallel data fetching + separate strategy loop
# Data हर 30 seconds में background में fetch होता रहेगा
# Strategy decisions तुरंत process होंगे without waiting for data

import logging
import time
import threading
from datetime import datetime, timedelta
import pandas as pd
import os
import importlib
import inspect
import pytz
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Import our centralized timezone configuration
from timezone_config import timezone_manager, now_ist, is_market_open, to_ist

# Import broker interfaces at the top level
from broker_interface import get_broker_interface, AngelOneInterface, ZerodhaInterface

# Load .env
load_dotenv()

def to_broker_interval(broker, minutes: int):
    """Map engine timeframe minutes to the broker's interval string."""
    if isinstance(broker, ZerodhaInterface):
        return f"{minutes}minute" if minutes < 60 else "day"
    if isinstance(broker, AngelOneInterface):
        return AngelOneInterface.INTERVAL_MAP.get(minutes, "FIFTEEN_MINUTE")
    return "FIFTEEN_MINUTE"

from config_loader import CONFIG
from database_manager import DatabaseManager
from trade_logger import TradeLogger
from strategies.base_strategy import BaseStrategy
from portfolio_manager import PortfolioManager

# --- SETUP ---
HEARTBEAT_FILE = "heartbeat.txt"
PARAMS_FILE = "live_params.json"
if not os.path.exists('logs'): os.makedirs('logs')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("logs/papertrading.log", encoding='utf-8'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# --- GLOBAL DATA STORAGE ---
class DataManager:
    """Thread-safe data manager for real-time data"""
    def __init__(self):
        self.all_data_1min = {}
        self.data_lock = threading.Lock()
        self.last_update_time = {}
        
    def update_symbol_data(self, symbol, new_data):
        """Thread-safe data update"""
        with self.data_lock:
            if symbol in self.all_data_1min:
                if not new_data.empty:
                    combined = pd.concat([self.all_data_1min[symbol], new_data]).sort_index()
                    combined = combined[~combined.index.duplicated(keep="last")]
                    self.all_data_1min[symbol] = combined
                    self.last_update_time[symbol] = datetime.now()
            else:
                self.all_data_1min[symbol] = new_data
                self.last_update_time[symbol] = datetime.now()
    
    def get_symbol_data(self, symbol):
        """Thread-safe data retrieval"""
        with self.data_lock:
            return self.all_data_1min.get(symbol, pd.DataFrame()).copy()
    
    def get_all_symbols(self):
        """Get list of all symbols"""
        with self.data_lock:
            return list(self.all_data_1min.keys())

# Global data manager instance
data_manager = DataManager()

def load_live_parameters():
    """Load parameters from live_params.json"""
    if not os.path.exists(PARAMS_FILE):
        logger.warning(f"{PARAMS_FILE} not found. Using default parameters.")
        return {}
    try:
        with open(PARAMS_FILE, "r") as f:
            data = json.load(f)
        logger.info(f"Successfully loaded live parameters from {PARAMS_FILE}")
        return data
    except Exception as e:
        logger.error(f"Error loading {PARAMS_FILE}: {e}. Using default parameters.")
        return {}

def check_broker_connection():
    """Check broker connection status before starting"""
    try:
        if os.path.exists("broker_status.txt"):
            with open("broker_status.txt", "r") as f:
                status = f.read().strip()
            if "CONNECTED" in status:
                logger.info(f"✅ Broker connection verified: {status}")
                return True
            else:
                logger.warning(f"⚠️ Broker connection issue: {status}")
        else:
            logger.warning("⚠️ Broker status file not found - running broker connection check...")
            # Run broker connection check
            result = os.system("./auto_broker_connect.sh")
            if result == 0:
                logger.info("✅ Broker connection established successfully")
                return True
            else:
                logger.error("❌ Failed to establish broker connection")
        
    except Exception as e:
        logger.error(f"Error checking broker connection: {e}")
    
    logger.warning("Continuing with trading bot startup despite broker connection issues...")
    return False

def fetch_single_symbol_data(broker, symbol, kolkata_tz=None):
    """Fetch data for a single symbol with timezone-aware handling and exponential backoff"""
    try:
        # Use centralized timezone management
        if kolkata_tz is None:
            kolkata_tz = timezone_manager.IST
            
        symbol_df = data_manager.get_symbol_data(symbol)
        
        if not symbol_df.empty:
            # Incremental fetch (small data, safe for parallel)
            last_dt = symbol_df.index[-1].to_pydatetime()
            if last_dt.tzinfo is None:
                last_dt = timezone_manager.to_ist(last_dt)
            from_date_live = last_dt + timedelta(minutes=1)
        else:
            # Initial fetch - reduced to 2 days to avoid huge requests
            from_date_live = now_ist() - timedelta(days=2)
        
        to_date = now_ist()
        
        # Skip if no new data needed
        if from_date_live >= to_date:
            return True
            
        # Exponential backoff for rate limit handling
        max_retries = 3
        base_delay = 1  # Start with 1 second
        
        for attempt in range(max_retries):
            try:
                new_data = broker.get_historical_data(
                    symbol, 
                    to_broker_interval(broker, 1), 
                    from_date_live, 
                    to_date
                )
                
                if new_data is not None and not new_data.empty:
                    new_data = new_data.sort_values("datetime")
                    new_data.set_index("datetime", inplace=True)
                    data_manager.update_symbol_data(symbol, new_data)
                    logger.debug(f"📊 Updated {len(new_data)} bars for {symbol}")
                
                return True  # Success
                
            except Exception as e:
                error_msg = str(e)
                if "Too many requests" in error_msg or "429" in error_msg:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                        logger.warning(f"⚠️ Rate limit hit for {symbol}, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"❌ Rate limit exceeded for {symbol} after {max_retries} attempts")
                        return False
                else:
                    # Non-rate-limit error, don't retry
                    logger.error(f"❌ Error fetching data for {symbol}: {e}")
                    return False
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Error fetching data for {symbol}: {e}")
        return False

def data_fetcher_thread(broker, symbols, kolkata_tz, stop_event):
    """Background thread to continuously fetch data with smart batching to prevent rate limiting"""
    logger.info("🔄 Data fetcher thread started with smart batching (rate limit prevention)")
    
    # Smart batching configuration to prevent "Too many requests"
    BATCH_SIZE = 5  # Reduced to 5 symbols per batch for extra safety
    DELAY_BETWEEN_BATCHES = 15  # Increased to 15 seconds between batches
    
    while not stop_event.is_set():
        try:
            start_time = time.time()
            successful_fetches = 0
            failed_fetches = 0
            
            logger.info(f"🔄 Starting smart batched data fetch for {len(symbols)} symbols")
            logger.info(f"📊 Batch size: {BATCH_SIZE}, Delay: {DELAY_BETWEEN_BATCHES}s")
            
            # Process all symbols in smart batches
            for i in range(0, len(symbols), BATCH_SIZE):
                if stop_event.is_set():
                    break
                    
                # Create current batch
                current_batch = symbols[i:i + BATCH_SIZE]
                batch_number = (i // BATCH_SIZE) + 1
                total_batches = (len(symbols) + BATCH_SIZE - 1) // BATCH_SIZE
                
                logger.info(f"📦 Processing batch {batch_number}/{total_batches}: {len(current_batch)} symbols")
                
                # Process batch concurrently (safe within batch size)
                batch_successful = 0
                batch_failed = 0
                
                with ThreadPoolExecutor(max_workers=min(len(current_batch), 5)) as executor:
                    future_to_symbol = {
                        executor.submit(fetch_single_symbol_data, broker, symbol, kolkata_tz): symbol 
                        for symbol in current_batch
                    }
                    
                    for future in as_completed(future_to_symbol):
                        if stop_event.is_set():
                            break
                        try:
                            success = future.result()
                            if success:
                                batch_successful += 1
                                successful_fetches += 1
                            else:
                                batch_failed += 1
                                failed_fetches += 1
                        except Exception as e:
                            batch_failed += 1
                            failed_fetches += 1
                            symbol = future_to_symbol.get(future, 'unknown')
                            logger.debug(f"❌ Failed to fetch {symbol}: {e}")
                
                logger.info(f"✅ Batch {batch_number} complete: {batch_successful} success, {batch_failed} failed")
                
                # Wait between batches (except for the last batch)
                if i + BATCH_SIZE < len(symbols) and not stop_event.is_set():
                    logger.info(f"⏳ Waiting {DELAY_BETWEEN_BATCHES}s before next batch to respect rate limits...")
                    time.sleep(DELAY_BETWEEN_BATCHES)
            
            fetch_duration = time.time() - start_time
            logger.info(f"📈 Data fetch completed in {fetch_duration:.2f}s: {successful_fetches} success, {failed_fetches} failed")
            
            # Wait for next cycle (60 seconds total)
            sleep_time = max(0, 60 - fetch_duration)
            if sleep_time > 0:
                stop_event.wait(sleep_time)
                
        except Exception as e:
            logger.error(f"Error in data fetcher: {e}")
            stop_event.wait(10)  # Wait 10s before retry

def load_strategies_and_data(live_params):
    """Load strategies and get initial symbol list"""
    strategy_instances = []
    all_symbols_needed = set()
    strategy_capital = {name: conf['capital'] for name, conf in CONFIG['strategy_config'].items()}
    
    # Collect all symbols
    for conf in CONFIG['strategy_config'].values():
        for symbol in conf['symbols']:
            all_symbols_needed.add(symbol)
    
    # Load initial data for all symbols
    logger.info(f"📊 Loading initial data for {len(all_symbols_needed)} symbols")
    kolkata_tz = timezone_manager.IST
    
    # Load strategy classes
    strategy_dir = "strategies"
    for file in os.listdir(strategy_dir):
        if not (file.endswith(".py") and not file.startswith("__")): 
            continue
            
        module_name = f"{strategy_dir}.{file[:-3]}"
        try:
            module = importlib.import_module(module_name)
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if (issubclass(cls, BaseStrategy) and 
                    cls is not BaseStrategy and 
                    name in CONFIG['strategy_config']):
                    
                    conf = CONFIG['strategy_config'][name]
                    timeframe = conf['timeframe']
                    
                    # Get parameters
                    strategy_base_params = conf.get('params', {})
                    strategy_live_params = live_params.get(name, {}).get('best_params', {})
                    final_params = {**strategy_base_params, **strategy_live_params}
                    
                    for symbol in conf['symbols']:
                        # Create strategy instance without data first
                        # Data will be provided by data manager
                        empty_df = pd.DataFrame()
                        instance = cls(
                            df=empty_df, 
                            symbol=symbol, 
                            primary_timeframe=timeframe, 
                            **final_params
                        )
                        strategy_instances.append(instance)
                        
                        if strategy_live_params:
                            logger.info(f"✅ Initialized '{name}' on '{symbol}' with LIVE parameters")
                        else:
                            logger.info(f"⚙️ Initialized '{name}' on '{symbol}' with DEFAULT parameters")
                            
        except Exception as e:
            logger.error(f"❌ Failed to load module {module_name}: {e}")

    return strategy_instances, list(all_symbols_needed), strategy_capital

def update_heartbeat():
    """Updates the heartbeat file"""
    with open(HEARTBEAT_FILE, "w") as f: 
        f.write(datetime.now().isoformat())

def check_control_signal():
    """Check for control signals"""
    if os.path.exists('control_signal.txt'):
        with open('control_signal.txt', 'r') as f: 
            return f.read().strip().upper()
    return "RUN"

def strategy_processor_thread(strategy_instances, portfolio, trade_logger, kolkata_tz, stop_event):
    """Main strategy processing thread - runs every 5 seconds"""
    logger.info("🧠 Strategy processor thread started")
    
    trading_start_time = CONFIG['trading_session']['start_time_obj']
    trading_end_time = CONFIG['trading_session']['end_time_obj']
    eod_tsl_start_time = CONFIG['execution']['risk_management']['aggressive_tsl_start_time_obj']
    final_exit_time = CONFIG['execution']['risk_management']['final_exit_time_obj']
    
    while not stop_event.is_set():
        try:
            update_heartbeat()
            
            if check_control_signal() == "STOP":
                logger.warning("🛑 STOP signal received")
                stop_event.wait(5)
                continue

            now_aware = now_ist()
            is_market_hours = trading_start_time <= now_aware.time() < trading_end_time
            is_weekday = now_aware.weekday() < 5

            if is_market_hours and is_weekday:
                logger.debug("📈 Market OPEN - Processing strategies")
                
                # Process each strategy with latest data
                for strategy in strategy_instances:
                    try:
                        symbol = strategy.symbol
                        symbol_df = data_manager.get_symbol_data(symbol)
                        
                        if symbol_df.empty:
                            logger.debug(f"⚠️ No data available for {symbol}")
                            continue

                        # Check for open positions
                        open_position = portfolio.get_open_position(strategy.name, symbol)
                        current_price = symbol_df.iloc[-1]['close']
                        
                        if open_position:
                            # Position management
                            if now_aware.time() < eod_tsl_start_time:
                                portfolio.update_position_price_and_sl(strategy.name, symbol, current_price)
                            
                            # Check exit conditions
                            active_pos = portfolio.get_open_position(strategy.name, symbol)
                            if active_pos:
                                active_stop_loss = active_pos['stop_loss']
                                target_price = active_pos['target']
                                exit_signal = False
                                
                                if open_position['action'] == 'LONG':
                                    if current_price <= active_stop_loss or current_price >= target_price:
                                        exit_signal = True
                                elif open_position['action'] == 'SHORT':
                                    if current_price >= active_stop_loss or current_price <= target_price:
                                        exit_signal = True
                                
                                if exit_signal:
                                    pnl = portfolio.close_position(strategy.name, symbol, current_price, now_aware)
                                    if pnl is not None:
                                        trade_logger.log_trade(
                                            now_aware, strategy.name, symbol, 
                                            f"EXIT_{open_position['action']}", 
                                            current_price, open_position['quantity'], 
                                            f"PnL: {pnl:.2f}"
                                        )
                                        logger.info(f"🎯 EXIT: {symbol} {open_position['action']} PnL: ₹{pnl:.2f}")
                        else:
                            # Entry signal detection
                            if now_aware.time() < final_exit_time:
                                # Update strategy with fresh data
                                strategy.df_1min_raw = symbol_df.copy()
                                signals_df = strategy.run()
                                
                                if not signals_df.empty:
                                    latest_candle = signals_df.iloc[-1]
                                    entry_signal = latest_candle.get('entry_signal')
                                    
                                    if entry_signal in ['LONG', 'SHORT']:
                                        action = entry_signal
                                        price = latest_candle['close']
                                        sl = latest_candle.get('stop_loss')
                                        tg = latest_candle.get('target')
                                        tsl_pct = latest_candle.get('trailing_sl_pct', 0.0)
                                        
                                        # Calculate position size
                                        available_cash = portfolio.cash.get(strategy.name, 0)
                                        position_value = available_cash * 0.1  # 10% allocation
                                        quantity = int(position_value / price)
                                        
                                        if quantity > 0:
                                            success = portfolio.record_trade(
                                                strategy.name, symbol, action, price, quantity, 
                                                now_aware, stop_loss=sl, target=tg, 
                                                trailing_sl_pct=tsl_pct
                                            )
                                            
                                            if success:
                                                trade_logger.log_trade(
                                                    now_aware, strategy.name, symbol, action, 
                                                    price, quantity, 
                                                    f"Entry: ₹{price:.2f}, SL: ₹{sl:.2f}, TG: ₹{tg:.2f}"
                                                )
                                                logger.info(f"🚀 ENTRY: {symbol} {action} {quantity}@₹{price:.2f}")
                                
                    except Exception as e:
                        logger.error(f"❌ Error processing strategy {strategy.name} for {symbol}: {e}")
                
                # Fast processing - check every 5 seconds
                stop_event.wait(5)
                
            else:
                logger.debug(f"🕒 Market CLOSED - Waiting ({now_aware.strftime('%H:%M:%S')})")
                stop_event.wait(60)
                
        except Exception as e:
            logger.error(f"❌ Error in strategy processor: {e}")
            stop_event.wait(10)

def run_optimized_paper_trader():
    """Main optimized trading function"""
    logger.info("🚀 OPTIMIZED Paper Trading System Initializing")
    db_manager = DatabaseManager()
    
    try:
        # Initialize broker
        broker = get_broker_interface(CONFIG)
        
        # Check credentials
        if isinstance(broker, ZerodhaInterface):
            z = CONFIG.get('zerodha', {})
            if not all([z.get('api_key'), z.get('api_secret'), z.get('access_token')]):
                logger.critical("❌ FATAL: Zerodha credentials missing")
                sys.exit(1)
        elif isinstance(broker, AngelOneInterface):
            a = CONFIG.get('angelone', {})
            if not all([a.get('api_key'), a.get('client_code')]):
                logger.critical("❌ FATAL: AngelOne credentials missing")
                sys.exit(1)

        # Load strategies and parameters
        live_params = load_live_parameters()
        strategy_instances, all_symbols, strategy_capital = load_strategies_and_data(live_params)
        
        if not strategy_instances:
            logger.error("❌ No strategies loaded. Exiting")
            return
            
        portfolio = PortfolioManager(db_manager=db_manager, strategy_capital=strategy_capital)
        trade_logger = TradeLogger(db_manager=db_manager)
        kolkata_tz = timezone_manager.IST

        logger.info(f"✅ System initialized with {len(strategy_instances)} strategies on {len(all_symbols)} symbols")
        
        # Create stop event for threads
        stop_event = threading.Event()
        
        # Start background data fetcher thread
        data_thread = threading.Thread(
            target=data_fetcher_thread,
            args=(broker, all_symbols, kolkata_tz, stop_event),
            daemon=True
        )
        data_thread.start()
        logger.info("🔄 Data fetcher thread started")
        
        # Wait a bit for initial data
        time.sleep(10)
        
        # Start strategy processor thread
        strategy_thread = threading.Thread(
            target=strategy_processor_thread,
            args=(strategy_instances, portfolio, trade_logger, kolkata_tz, stop_event),
            daemon=True
        )
        strategy_thread.start()
        logger.info("🧠 Strategy processor thread started")
        
        # Main thread - just monitors and handles shutdown
        logger.info("✅ ALL SYSTEMS RUNNING - Press Ctrl+C to stop")
        try:
            while True:
                time.sleep(60)  # Check every minute
                logger.info(f"💗 System alive - {datetime.now().strftime('%H:%M:%S')}")
                
        except KeyboardInterrupt:
            logger.info("🛑 User interrupted. Shutting down...")
            stop_event.set()
            
            # Wait for threads to finish
            data_thread.join(timeout=5)
            strategy_thread.join(timeout=5)
            
    except Exception as e:
        logger.error(f"❌ Critical error: {e}", exc_info=True)
    finally:
        db_manager.close_connection()
        # Cleanup files
        for file in ['control_signal.txt', 'exit_command.txt', HEARTBEAT_FILE]:
            if os.path.exists(file): 
                os.remove(file)
        logger.info("🏁 Paper Trading System Stopped")

def main():
    logger.info("🚀 Initializing OPTIMIZED Paper Trading Engine")
    
    # Check broker connection before starting
    logger.info("🔗 Checking broker connection status...")
    check_broker_connection()
    
    run_optimized_paper_trader()

if __name__ == "__main__":
    main()
