# main_papertrader.py
# FINAL INTEGRATED VERSION: Yeh aapke advanced, multi-strategy engine ko
# dynamic 'live_params.json' ke saath jodta hai.

import logging
import time
from datetime import datetime, timedelta
import pandas as pd
import os
import importlib
import inspect
import pytz
import sys
import json
from dotenv import load_dotenv

# Import broker interfaces at the top level
from broker_interface import get_broker_interface, AngelOneInterface, ZerodhaInterface

# Load .env
load_dotenv()

def to_broker_interval(broker, minutes: int):
    """Map engine timeframe minutes to the broker's interval string."""
    # Zerodha: '15minute', 'day' etc.
    if isinstance(broker, ZerodhaInterface):
        return f"{minutes}minute" if minutes < 60 else "day"
    # AngelOne: enum names
    if isinstance(broker, AngelOneInterface):
        return AngelOneInterface.INTERVAL_MAP.get(minutes, "FIFTEEN_MINUTE")
    return "FIFTEEN_MINUTE"

# --- Updated Import ---
from config_loader import CONFIG
from database_manager import DatabaseManager
from trade_logger import TradeLogger
from strategies.base_strategy import BaseStrategy
from portfolio_manager import PortfolioManager

# --- 1. SETUP ---
HEARTBEAT_FILE = "heartbeat.txt"
PARAMS_FILE = "live_params.json" # Parameters file ka naam
if not os.path.exists('logs'): os.makedirs('logs')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("logs/papertrading.log", encoding='utf-8'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# --- 2. HELPER FUNCTIONS ---

# --- YAHAN BADLAV KIYA GAYA HAI: Naya, Smart Parameter Loader ---
def load_live_parameters():
    """
    live_params.json file se sabhi strategies ke liye best parameters load karta hai.
    """
    if not os.path.exists(PARAMS_FILE):
        logger.warning(f"{PARAMS_FILE} not found. Using default parameters from config.yml for all strategies.")
        return {}
    try:
        with open(PARAMS_FILE, "r") as f:
            data = json.load(f)
        logger.info(f"Successfully loaded live parameters from {PARAMS_FILE}")
        return data
    except Exception as e:
        logger.error(f"Error loading {PARAMS_FILE}: {e}. Using default parameters.")
        return {}
# --- END OF BADLAV ---


def load_strategies_and_data(broker, live_params):
    """
    Sabhi strategies aur unke data ko load karta hai, ab live parameters ka istemaal karke.
    """
    strategy_instances = []
    all_symbols_needed = set()
    strategy_capital = {name: conf['capital'] for name, conf in CONFIG['strategy_config'].items()}
    
    for conf in CONFIG['strategy_config'].values():
        for symbol in conf['symbols']:
            all_symbols_needed.add(symbol)
    
    all_data_1min = {}
    kolkata_tz = pytz.timezone('Asia/Kolkata')
    for symbol in all_symbols_needed:
        to_date = datetime.now(kolkata_tz)
        from_date = to_date - timedelta(days=10) 
        df = broker.get_historical_data(symbol, to_broker_interval(broker, 1), from_date, to_date)
        if df is not None and not df.empty:
            df = df.sort_values("datetime")
            df.set_index("datetime", inplace=True)
            all_data_1min[symbol] = df

    strategy_dir = "strategies"
    for file in os.listdir(strategy_dir):
        if not (file.endswith(".py") and not file.startswith("__")): continue
        module_name = f"{strategy_dir}.{file[:-3]}"
        try:
            module = importlib.import_module(module_name)
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, BaseStrategy) and cls is not BaseStrategy and name in CONFIG['strategy_config']:
                    conf = CONFIG['strategy_config'][name]
                    timeframe = conf['timeframe']
                    
                    # --- YAHAN BADLAV KIYA GAYA HAI: Strategy-specific parameters ko jodein ---
                    strategy_base_params = conf.get('params', {})
                    strategy_live_params = live_params.get(name, {}).get('best_params', {})
                    final_params = {**strategy_base_params, **strategy_live_params} # Live params default ko override karenge
                    # --- END OF BADLAV ---

                    for symbol in conf['symbols']:
                        raw_df = all_data_1min.get(symbol)
                        if raw_df is not None and not raw_df.empty:
                            # Strategy ko final (updated) parameters ke saath initialize karein
                            instance = cls(df=raw_df.copy(), symbol=symbol, primary_timeframe=timeframe, **final_params)
                            strategy_instances.append(instance)
                            if strategy_live_params:
                                logger.info(f"Initialized '{name}' on '{symbol}' with LIVE parameters: {strategy_live_params}")
                            else:
                                logger.info(f"Initialized '{name}' on '{symbol}' with DEFAULT parameters.")
        except Exception as e:
            logger.error(f"Failed to load or instantiate from module {module_name}: {e}")

    return strategy_instances, all_data_1min, strategy_capital

# ... (baaki saare helper functions waise hi rahenge) ...
def update_heartbeat():
    """Updates the heartbeat file to indicate the engine is live."""
    with open(HEARTBEAT_FILE, "w") as f: f.write(datetime.now().isoformat())

def check_control_signal():
    """Checks for a RUN/STOP signal from the dashboard."""
    if os.path.exists('control_signal.txt'):
        with open('control_signal.txt', 'r') as f: return f.read().strip().upper()
    return "RUN"

def handle_eod_aggressive_tsl(portfolio, all_data_1min):
    logger.info("Aggressive EOD TSL management starting for all open positions...")
    eod_tsl_pct = CONFIG['execution']['risk_management']['eod_aggressive_tsl_pct']
    for strategy_name in list(portfolio.positions.keys()):
        if strategy_name not in portfolio.positions: continue
        for symbol, position in list(portfolio.positions[strategy_name].items()):
            symbol_df = all_data_1min.get(symbol)
            if symbol_df is not None and not symbol_df.empty:
                current_price = symbol_df.iloc[-1]['close']
            else:
                logger.warning(f"EOD TSL: Could not get current price for {symbol}. Skipping.")
                continue
            action = position['action']
            new_sl = 0
            if action == 'LONG':
                new_sl = current_price * (1 - eod_tsl_pct)
                position['stop_loss'] = max(position.get('stop_loss', 0), new_sl)
            elif action == 'SHORT':
                new_sl = current_price * (1 + eod_tsl_pct)
                position['stop_loss'] = min(position.get('stop_loss', float('inf')), new_sl)
            logger.info(f"EOD AGGRESSIVE TSL for {symbol}: SL updated to {position['stop_loss']:.2f}")


# --- 3. MAIN TRADING FUNCTION ---
def run_paper_trader():
    logger.info("--- Paper Trading System Initializing ---")
    db_manager = DatabaseManager()
    try:
        # First create the broker interface dynamically
        # 'broker' value config.yml se aayega, jise config_loader load karta hai
        broker = get_broker_interface(CONFIG)
        
        # Then check credentials only if it's a specific broker type
        if isinstance(broker, ZerodhaInterface):
            z = CONFIG.get('zerodha', {})
            if not all([z.get('api_key'), z.get('api_secret'), z.get('access_token')]):
                logger.critical("FATAL: Zerodha credentials missing (api_key/api_secret/access_token).")
                sys.exit(1)
        elif isinstance(broker, AngelOneInterface):
            a = CONFIG.get('angelone', {})
            if not all([a.get('api_key'), a.get('client_code')]):
                logger.critical("FATAL: AngelOne credentials missing (api_key/client_code).")
                sys.exit(1)

        live_params = load_live_parameters()
        strategy_instances, all_data_1min, strategy_capital = load_strategies_and_data(broker, live_params)
        
        if not strategy_instances:
            logger.error("No strategies loaded. Exiting."); return
            
        portfolio = PortfolioManager(db_manager=db_manager, strategy_capital=strategy_capital)
        trade_logger = TradeLogger(db_manager=db_manager)
        
        kolkata_tz = pytz.timezone('Asia/Kolkata')

        trading_start_time = CONFIG['trading_session']['start_time_obj']
        trading_end_time = CONFIG['trading_session']['end_time_obj']
        eod_tsl_start_time = CONFIG['execution']['risk_management']['aggressive_tsl_start_time_obj']
        final_exit_time = CONFIG['execution']['risk_management']['final_exit_time_obj']

        logger.info("--- System Initialized. Starting Main Loop ---")
        while True:
            # ... (Aapka poora main trading loop logic yahan waise hi rahega) ...
            try:
                update_heartbeat()
                if check_control_signal() == "STOP":
                    logger.warning("STOP signal received. Pausing engine.")
                    time.sleep(5)
                    continue

                now_aware = datetime.now(kolkata_tz)
                is_market_hours = trading_start_time <= now_aware.time() < trading_end_time
                is_weekday = now_aware.weekday() < 5

                if is_market_hours and is_weekday:
                    logger.info("Market is OPEN. Scanning for signals...")
                    
                    for symbol in all_data_1min.keys():
                        symbol_df = all_data_1min.get(symbol)
                        if symbol_df is not None and not symbol_df.empty:
                            latest_timestamp = symbol_df.index[-1]
                            # When calculating the next fetch time:
                            last_dt = all_data_1min[symbol].index[-1].to_pydatetime()
                            if last_dt.tzinfo is None:
                                last_dt = pytz.timezone("Asia/Kolkata").localize(last_dt)
                            from_date_live = last_dt + timedelta(minutes=1)
                            if from_date_live < now_aware:
                                new_data = broker.get_historical_data(symbol, to_broker_interval(broker, 1), from_date=from_date_live, to_date=now_aware)
                                if not new_data.empty:
                                    new_data = new_data.sort_values("datetime").set_index("datetime")
                                    combined = pd.concat([all_data_1min[symbol], new_data]).sort_index()
                                    combined = combined[~combined.index.duplicated(keep="last")]
                                    all_data_1min[symbol] = combined
                    
                    if eod_tsl_start_time <= now_aware.time() < final_exit_time:
                        handle_eod_aggressive_tsl(portfolio, all_data_1min)
                    
                    if now_aware.time() >= final_exit_time:
                        logger.warning(f"FINAL EXIT TIME ({final_exit_time.strftime('%H:%M')}) REACHED. Closing loss-making positions.")
                        for strategy_name in list(portfolio.positions.keys()):
                            for symbol, position in list(portfolio.positions[strategy_name].items()):
                                symbol_df = all_data_1min.get(symbol)
                                if symbol_df is not None and not symbol_df.empty:
                                    current_price = symbol_df.iloc[-1]['close']
                                else:
                                    current_price = position['entry_price'] 
                                    logger.error(f"Could not get final price for {symbol}, using entry price for PnL check.")
                                
                                entry_price = position['entry_price']
                                action = position['action']
                                current_pnl_pct = ((current_price - entry_price) / entry_price) if action == 'LONG' else ((entry_price - current_price) / entry_price)

                                if current_pnl_pct < 0:
                                    pnl = portfolio.close_position(strategy_name, symbol, current_price, now_aware)
                                    if pnl is not None:
                                        trade_logger.log_trade(now_aware, strategy_name, symbol, f"FINAL_EXIT_LOSS_{position['action']}", current_price, position['quantity'], f"Forced EOD Loss Cut. PnL: {pnl:.2f}")
                                else:
                                    logger.info(f"CARRY FORWARD: Profitable trade for {symbol} will be carried forward to the next day.")

                        logger.info("EOD check complete. Waiting for market to close.")
                        time.sleep(120) 
                        continue

                    for strategy in strategy_instances:
                        symbol = strategy.symbol
                        symbol_df = all_data_1min.get(symbol)
                        if symbol_df is None or symbol_df.empty:
                            continue

                        if portfolio.get_open_position(strategy.name, symbol):
                            open_position = portfolio.get_open_position(strategy.name, symbol)
                            current_price = symbol_df.iloc[-1]['close']
                            
                            if now_aware.time() < eod_tsl_start_time:
                                portfolio.update_position_price_and_sl(strategy.name, symbol, current_price)
                            
                            active_pos = portfolio.get_open_position(strategy.name, symbol)
                            if active_pos:
                                active_stop_loss, target_price = active_pos['stop_loss'], active_pos['target']
                                exit_signal = False
                                if open_position['action'] == 'LONG' and (current_price <= active_stop_loss or current_price >= target_price):
                                    exit_signal = True
                                elif open_position['action'] == 'SHORT' and (current_price >= active_stop_loss or current_price <= target_price):
                                    exit_signal = True
                                
                                if exit_signal:
                                    pnl = portfolio.close_position(strategy.name, symbol, current_price, now_aware)
                                    if pnl is not None:
                                        trade_logger.log_trade(now_aware, strategy.name, symbol, f"EXIT_{open_position['action']}", current_price, open_position['quantity'], f"PnL: {pnl:.2f}")
                        else:
                            if now_aware.time() < final_exit_time:
                                strategy.df_1min_raw = symbol_df.copy()
                                signals_df = strategy.run()
                                if not signals_df.empty:
                                    latest_candle = signals_df.iloc[-1]
                                    if latest_candle.get('entry_signal') in ['LONG', 'SHORT']:
                                        action, price, sl, tg, tsl_pct = (latest_candle['entry_signal'], latest_candle['close'], latest_candle.get('stop_loss'), latest_candle.get('target'), latest_candle.get('trailing_sl_pct', 0.0))
                                        quantity = int((portfolio.cash.get(strategy.name, 0) * 0.1) / price)
                                        if quantity > 0:
                                            success = portfolio.record_trade(strategy.name, symbol, action, price, quantity, now_aware, stop_loss=sl, target=tg, trailing_sl_pct=tsl_pct)
                                            if success:
                                                trade_logger.log_trade(now_aware, strategy.name, symbol, action, price, quantity, f"Cash Left: {portfolio.cash[strategy.name]:.2f}")
                    
                    sleep_duration = CONFIG['execution']['main_loop_sleep_seconds']
                    time.sleep(sleep_duration)
                else:
                    logger.info(f"Market is CLOSED. Waiting... ({now_aware.strftime('%H:%M:%S')})")
                    time.sleep(60)

            except KeyboardInterrupt:
                logger.info("User interrupted. Shutting down."); break
            except Exception as e:
                logger.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
                time.sleep(30)
    finally:
        db_manager.close_connection()
        for file in ['control_signal.txt', 'exit_command.txt', HEARTBEAT_FILE]:
            if os.path.exists(file): os.remove(file)
        logger.info("--- Paper Trading System Stopped ---")

def main():
    logger.info("--- Initializing Paper Trading Engine with YAML Config ---")
    run_paper_trader()

if __name__ == "__main__":
    main()
