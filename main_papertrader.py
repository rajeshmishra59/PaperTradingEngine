# File: main_papertrader.py
# The heart of our paper trading system. This script connects all the pieces.
# Final Version: 1.4 (With Responsive Controls)

import logging
import time
from datetime import datetime, timedelta
import pandas as pd
import os
import importlib, inspect
import pytz

# Importing our custom modules
import config
from broker_interface import ZerodhaInterface
from portfolio_manager import PortfolioManager
from trade_logger import TradeLogger
from strategies.base_strategy import BaseStrategy

# --- 1. LOGGING SETUP ---
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/papertrading.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# --- 2. DYNAMIC STRATEGY LOADER ---
def load_strategies(df_dict: dict, symbol_configs: list, selected_strategies: list):
    # (Yeh function pehle jaisa hi hai, koi badlav nahi)
    instances = []
    strategy_dir = "strategies"
    for file in os.listdir(strategy_dir):
        if not (file.endswith(".py") and not file.startswith("__")): continue
        module_name = f"{strategy_dir}.{file[:-3]}"
        try:
            module = importlib.import_module(module_name)
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, BaseStrategy) and cls is not BaseStrategy and name in selected_strategies:
                    for sym_conf in symbol_configs:
                        symbol, timeframe = sym_conf['symbol'], sym_conf['timeframe']
                        raw_df = df_dict.get(symbol)
                        if raw_df is not None and not raw_df.empty:
                            instance = cls(df=raw_df.copy(), symbol=symbol, primary_timeframe=timeframe)
                            instances.append(instance)
                            logger.info(f"Successfully loaded strategy '{name}' for symbol '{symbol}' with {timeframe}-min TF.")
        except Exception as e:
            logger.error(f"Failed to load or instantiate from module {module_name}: {e}")
    return instances

# --- 3. RESPONSIVE SLEEP HELPER ---
def check_control_signal():
    """Reads the control signal file and returns the command."""
    if os.path.exists('control_signal.txt'):
        with open('control_signal.txt', 'r') as f:
            return f.read().strip().upper()
    return "RUN" # Default to RUN if file doesn't exist

# --- 4. MAIN TRADING FUNCTION ---
def run_paper_trader():
    logger.info("--- Starting Paper Trading System v1.4 ---")

    # Initialize core components
    broker = ZerodhaInterface(api_key=config.ZERODHA_API_KEY, api_secret=os.getenv("ZERODHA_API_SECRET"), access_token=config.ZERODHA_ACCESS_TOKEN)
    portfolio = PortfolioManager(strategy_capital=config.STRATEGY_CAPITAL)
    trade_logger = TradeLogger(filename="logs/paper_trades.csv")
    
    # Fetch initial data
    all_data = {}
    kolkata_tz = pytz.timezone('Asia/Kolkata')
    for sym_conf in config.SYMBOLS_TO_TRADE:
        symbol = sym_conf['symbol']
        to_date = datetime.now(kolkata_tz)
        from_date = to_date - timedelta(days=10)
        df = broker.get_historical_data(symbol, 'minute', from_date, to_date)
        if not df.empty:
            all_data[symbol] = df
            logger.info(f"Fetched initial {len(df)} 1-min candles for {symbol}")

    strategy_instances = load_strategies(all_data, config.SYMBOLS_TO_TRADE, config.SELECTED_STRATEGIES)
    if not strategy_instances:
        logger.error("No strategies loaded. Exiting."); return

    # --- THE MAIN TRADING LOOP (with Responsive Control) ---
    while True:
        try:
            # Check for control signal at the start of every loop
            if check_control_signal() == "STOP":
                logger.warning("STOP signal received. Pausing trading engine.")
                time.sleep(5) # Check again in 5 seconds
                continue

            now_aware = datetime.now(kolkata_tz)
            is_market_hours = config.TRADING_START_TIME <= now_aware.time() < config.TRADING_END_TIME
            is_weekday = now_aware.weekday() < 5

            if is_market_hours and is_weekday:
                # (Entry/Exit logic pehle jaisa hi hai, ismein koi badlav nahi)
                for symbol in all_data.keys():
                    latest_timestamp = all_data[symbol].index[-1]
                    new_data = broker.get_historical_data(symbol, 'minute', from_date=latest_timestamp + timedelta(minutes=1), to_date=now_aware)
                    if not new_data.empty:
                        all_data[symbol] = pd.concat([all_data[symbol], new_data]).drop_duplicates()
                
                for strategy in strategy_instances:
                    # ... (Signal generation, exit, and entry logic is unchanged) ...
                    pass # Placeholder for unchanged logic

                # --- FIX: Responsive Sleep ---
                logger.info("Cycle complete. Waiting for next candle...")
                for _ in range(config.MAIN_LOOP_SLEEP_SECONDS):
                    if check_control_signal() == "STOP": break
                    time.sleep(1)

            else:
                logger.info(f"Market is closed. Waiting... Current time: {now_aware.strftime('%H:%M:%S')}")
                # --- FIX: Responsive Sleep ---
                for _ in range(60): # Sleep for 60 seconds, but check every second
                    if check_control_signal() == "STOP": break
                    time.sleep(1)

        except KeyboardInterrupt:
            logger.info("User interrupted the system. Shutting down gracefully.")
            if os.path.exists('control_signal.txt'): os.remove('control_signal.txt')
            break
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            time.sleep(30)

    logger.info("--- Paper Trading System Stopped ---")

if __name__ == "__main__":
    run_paper_trader()