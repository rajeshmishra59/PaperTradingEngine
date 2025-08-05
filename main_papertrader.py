# File: main_papertrader.py (Final Version with Enhanced Logging)

import logging
import time
from datetime import datetime, timedelta
import pandas as pd
import os
import importlib
import inspect
import pytz

# Importing our custom modules
import config
from broker_interface import ZerodhaInterface
from database_manager import DatabaseManager
from portfolio_manager import PortfolioManager
from trade_logger import TradeLogger
from strategies.base_strategy import BaseStrategy

# --- 1. SETUP ---
HEARTBEAT_FILE = "heartbeat.txt"
if not os.path.exists('logs'): os.makedirs('logs')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("logs/papertrading.log", encoding='utf-8'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# --- 2. HELPER FUNCTIONS ---
def load_strategies_and_data(broker):
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
        from_date = to_date - timedelta(days=10)
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
    with open(HEARTBEAT_FILE, "w") as f: f.write(datetime.now().isoformat())

def check_control_signal():
    if os.path.exists('control_signal.txt'):
        with open('control_signal.txt', 'r') as f: return f.read().strip().upper()
    return "RUN"

def check_force_exit_command():
    if os.path.exists('exit_command.txt'):
        with open('exit_command.txt', 'r') as f: command = f.read().strip()
        os.remove('exit_command.txt')
        if command:
            try:
                strategy_name, symbol = command.split(','); return strategy_name, symbol
            except ValueError: logger.error(f"Invalid command in exit_command.txt: {command}")
    return None, None

# --- 3. MAIN TRADING FUNCTION ---
def run_paper_trader():
    logger.info("--- Starting Paper Trading System ---")
    db_manager = DatabaseManager()
    
    try:
        broker = ZerodhaInterface(api_key=config.ZERODHA_API_KEY, api_secret=os.getenv("ZERODHA_API_SECRET"), access_token=config.ZERODHA_ACCESS_TOKEN)
        strategy_instances, all_data_1min, strategy_capital = load_strategies_and_data(broker)
        
        if not strategy_instances:
            logger.error("No strategies loaded. Exiting."); return
            
        portfolio = PortfolioManager(db_manager=db_manager, strategy_capital=strategy_capital)
        trade_logger = TradeLogger(db_manager=db_manager)
        kolkata_tz = pytz.timezone('Asia/Kolkata')
        
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
                        latest_timestamp = all_data_1min[symbol].index[-1]
                        from_date_live = latest_timestamp.to_pydatetime().astimezone(kolkata_tz) + timedelta(minutes=1)
                        if from_date_live < now_aware:
                            new_data = broker.get_historical_data(symbol, 'minute', from_date=from_date_live, to_date=now_aware)
                            if not new_data.empty:
                                all_data_1min[symbol] = pd.concat([all_data_1min[symbol], new_data]).drop_duplicates()
                    
                    trades_found_this_cycle = 0
                    for strategy in strategy_instances:
                        symbol = strategy.symbol
                        df_1m = all_data_1min.get(symbol, pd.DataFrame()).copy()
                        if df_1m.empty: continue
                        
                        strategy.df_1min_raw = df_1m
                        signals_df = strategy.run()
                        if signals_df.empty: continue
                        
                        latest_candle, current_price = signals_df.iloc[-1], signals_df.iloc[-1]['close']
                        open_position = portfolio.get_open_position(strategy.name, symbol)
                        
                        if open_position:
                            portfolio.update_position_price_and_sl(strategy.name, symbol, current_price)
                            active_pos = portfolio.get_open_position(strategy.name, symbol)
                            if active_pos:
                                active_stop_loss, target_price = active_pos['stop_loss'], active_pos['target']
                                exit_signal = False
                                if open_position['action'] == 'LONG' and (current_price <= active_stop_loss or current_price >= target_price): exit_signal = True
                                elif open_position['action'] == 'SHORT' and (current_price >= active_stop_loss or current_price <= target_price): exit_signal = True
                                if exit_signal:
                                    pnl = portfolio.close_position(strategy.name, symbol, current_price, now_aware)
                                    if pnl is not None:
                                        trade_logger.log_trade(now_aware, strategy.name, symbol, f"EXIT_{open_position['action']}", current_price, open_position['quantity'], f"PnL: {pnl:.2f}")
                        else:
                            if latest_candle.get('entry_signal') in ['LONG', 'SHORT']:
                                action, price, sl, tg, tsl_pct = (latest_candle['entry_signal'], latest_candle['close'], latest_candle.get('stop_loss'), latest_candle.get('target'), latest_candle.get('trailing_sl_pct', 0.0))
                                quantity = int((portfolio.cash.get(strategy.name, 0) * 0.1) / price)
                                if quantity > 0:
                                    success = portfolio.record_trade(strategy.name, symbol, action, price, quantity, now_aware, stop_loss=sl, target=tg, trailing_sl_pct=tsl_pct)
                                    if success:
                                        trades_found_this_cycle += 1
                                        trade_logger.log_trade(now_aware, strategy.name, symbol, action, price, quantity, f"Cash Left: {portfolio.cash[strategy.name]:.2f}")
                    
                    if trades_found_this_cycle == 0:
                        logger.info("Scan complete. No new trade opportunities found.")
                    else:
                        logger.info(f"Scan complete. Found and executed {trades_found_this_cycle} new trade(s).")

                    for _ in range(config.MAIN_LOOP_SLEEP_SECONDS):
                        if check_control_signal() == "STOP": break
                        time.sleep(1)
                else:
                    logger.info(f"Market is CLOSED. Waiting... ({now_aware.strftime('%H:%M:%S')})")
                    for _ in range(60):
                        if check_control_signal() == "STOP": break
                        time.sleep(1)

            except KeyboardInterrupt:
                logger.info("User interrupted. Shutting down."); break
            except Exception as e:
                logger.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True); time.sleep(30)
    finally:
        db_manager.close_connection()
        for file in ['control_signal.txt', 'exit_command.txt', HEARTBEAT_FILE]:
            if os.path.exists(file): os.remove(file)
        logger.info("--- Paper Trading System Stopped ---")

if __name__ == "__main__":
    run_paper_trader()