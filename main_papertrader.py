# File: main_papertrader.py (Final Version with Intraday-to-Swing (ITS) EOD Management)
# Yeh version sabhi errors ko fix karke aur code ko robust banakar taiyaar kiya gaya hai.

import logging
import time
from datetime import datetime, timedelta, time as dt_time
import pandas as pd
import os
import importlib
import inspect
import pytz
import sys # Graceful exit ke liye import karein

# Humare custom modules ko import karna
import config
from broker_interface import ZerodhaInterface
from database_manager import DatabaseManager
from portfolio_manager import PortfolioManager
from trade_logger import TradeLogger
from strategies.base_strategy import BaseStrategy

# --- 1. SETUP ---
HEARTBEAT_FILE = "heartbeat.txt"
if not os.path.exists('logs'): os.makedirs('logs')
# Logging setup taaki har activity ka record rahe
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("logs/papertrading.log", encoding='utf-8'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# --- 2. HELPER FUNCTIONS ---
def load_strategies_and_data(broker):
    """
    Saari strategies aur unke liye zaroori historical data ko shuruaat mein load karta hai.
    """
    strategy_instances = []
    all_symbols_needed = set()
    strategy_capital = {name: conf['capital'] for name, conf in config.STRATEGY_CONFIG.items()}
    
    for strategy_name, conf in config.STRATEGY_CONFIG.items():
        for symbol in conf['symbols']:
            all_symbols_needed.add(symbol)
    
    all_data_1min = {}
    kolkata_tz = pytz.timezone('Asia/Kolkata')
    for symbol in all_symbols_needed:
        to_date = datetime.now(kolkata_tz)
        from_date = to_date - timedelta(days=10) # Shuruaati data ke liye 10 din ka data fetch karein
        df = broker.get_historical_data(symbol, 'minute', from_date, to_date)
        if not df.empty:
            all_data_1min[symbol] = df
            logger.info(f"Fetched initial {len(df)} 1-min candles for {symbol}")

    strategy_dir = "strategies"
    for file in os.listdir(strategy_dir):
        if not (file.endswith(".py") and not file.startswith("__")): continue
        module_name = f"{strategy_dir}.{file[:-3]}"
        try:
            module = importlib.import_module(module_name)
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, BaseStrategy) and cls is not BaseStrategy and name in config.STRATEGY_CONFIG:
                    conf = config.STRATEGY_CONFIG[name]
                    timeframe = conf['timeframe']
                    for symbol in conf['symbols']:
                        raw_df = all_data_1min.get(symbol)
                        if raw_df is not None and not raw_df.empty:
                            instance = cls(df=raw_df.copy(), symbol=symbol, primary_timeframe=timeframe)
                            strategy_instances.append(instance)
                    logger.info(f"Successfully configured strategy '{name}' for {len(conf['symbols'])} symbols on {timeframe}-min TF.")
        except Exception as e:
            logger.error(f"Failed to load or instantiate from module {module_name}: {e}")

    return strategy_instances, all_data_1min, strategy_capital

def update_heartbeat():
    """Engine ke live status ke liye heartbeat file update karta hai."""
    with open(HEARTBEAT_FILE, "w") as f: f.write(datetime.now().isoformat())

def check_control_signal():
    """Dashboard se RUN/STOP signal check karta hai."""
    if os.path.exists('control_signal.txt'):
        with open('control_signal.txt', 'r') as f: return f.read().strip().upper()
    return "RUN"

def handle_eod_aggressive_tsl(portfolio, all_data_1min):
    """
    3:00 PM ke baad sabhi open positions par aggressive 0.1% TSL lagata hai.
    """
    logger.info("Aggressive EOD TSL management starting for all open positions...")
    
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
            
            # Logic: Sabhi trades par aggressive TSL lagayen
            new_sl = 0
            if action == 'LONG':
                new_sl = current_price * 0.999  # 0.1% TSL
                position['stop_loss'] = max(position.get('stop_loss', 0), new_sl)
            elif action == 'SHORT':
                new_sl = current_price * 1.001  # 0.1% TSL
                position['stop_loss'] = min(position.get('stop_loss', float('inf')), new_sl)
                
            logger.info(f"EOD AGGRESSIVE TSL for {symbol}: SL updated to {position['stop_loss']:.2f}")

# --- 3. MAIN TRADING FUNCTION ---
def run_paper_trader(api_key: str, api_secret: str, access_token: str):
    """
    Yeh function ab saare trading logic ko chalata hai, yeh maante hue ki API keys sahi hain.
    """
    logger.info("--- Paper Trading System Initializing ---")
    db_manager = DatabaseManager()
    try:
        broker = ZerodhaInterface(api_key=api_key, api_secret=api_secret, access_token=access_token)
        
        strategy_instances, all_data_1min, strategy_capital = load_strategies_and_data(broker)
        
        if not strategy_instances:
            logger.error("No strategies loaded. Exiting."); return
            
        portfolio = PortfolioManager(db_manager=db_manager, strategy_capital=strategy_capital)
        trade_logger = TradeLogger(db_manager=db_manager)
        kolkata_tz = pytz.timezone('Asia/Kolkata')
        
        eod_tsl_start_time = dt_time(15, 0)
        final_exit_time = dt_time(15, 20)

        logger.info("--- System Initialized. Starting Main Loop ---")
        while True:
            try:
                update_heartbeat()
                
                if check_control_signal() == "STOP":
                    logger.warning("STOP signal received. Pausing engine.")
                    time.sleep(5)
                    continue

                now_aware = datetime.now(kolkata_tz)
                is_market_hours = config.TRADING_START_TIME <= now_aware.time() < config.TRADING_END_TIME
                is_weekday = now_aware.weekday() < 5

                if is_market_hours and is_weekday:
                    logger.info("Market is OPEN. Scanning for signals...")
                    
                    for symbol in all_data_1min.keys():
                        symbol_df = all_data_1min.get(symbol)
                        if symbol_df is not None and not symbol_df.empty:
                            latest_timestamp = symbol_df.index[-1]
                            from_date_live = latest_timestamp.to_pydatetime().astimezone(kolkata_tz) + timedelta(minutes=1)
                            if from_date_live < now_aware:
                                new_data = broker.get_historical_data(symbol, 'minute', from_date=from_date_live, to_date=now_aware)
                                if not new_data.empty:
                                    all_data_1min[symbol] = pd.concat([all_data_1min[symbol], new_data]).drop_duplicates()
                    
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
                                        trade_logger.log_trade(now_aware, strategy_name, symbol, f"EXIT_{open_position['action']}", current_price, open_position['quantity'], f"PnL: {pnl:.2f}")
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

                    time.sleep(config.MAIN_LOOP_SLEEP_SECONDS)
                else:
                    logger.info(f"Market is CLOSED. Waiting... ({now_aware.strftime('%H:%M:%S')})")
                    time.sleep(60)

            except KeyboardInterrupt:
                logger.info("User interrupted. Shutting down."); break
            except Exception as e:
                logger.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True); time.sleep(30)
    finally:
        db_manager.close_connection()
        for file in ['control_signal.txt', 'exit_command.txt', HEARTBEAT_FILE]:
            if os.path.exists(file): os.remove(file)
        logger.info("--- Paper Trading System Stopped ---")

def main():
    """
    Program ka entry point. API keys ki jaanch karta hai aur fir trading logic ko call karta hai.
    """
    logger.info("--- Validating Credentials ---")
    api_key = config.ZERODHA_API_KEY
    api_secret = config.ZERODHA_API_SECRET
    access_token = config.ZERODHA_ACCESS_TOKEN

    if not all([api_key, api_secret, access_token]):
        logger.critical("FATAL ERROR: API Key/Secret/Access Token not found in config.py. Please check your .env file and ensure it is loaded correctly. Exiting.")
        sys.exit(1)
    
    logger.info("✅ Credentials validated successfully.")
    # Agar sab theek hai, to trading engine chalu karein
    run_paper_trader(api_key, api_secret, access_token)

if __name__ == "__main__":
    main()
