# File: config.py (Updated "Best of Both Worlds" Version)

from datetime import time
import os
from dotenv import load_dotenv

# --- API KEY LOADING ---
# .env file se API credentials load karega
load_dotenv() 
ZERODHA_API_KEY = os.getenv("ZERODHA_API_KEY")
ZERODHA_ACCESS_TOKEN = os.getenv("ZERODHA_ACCESS_TOKEN")

# --- TRADING SESSION (from new config) ---
TRADING_START_TIME = time(9, 15)
TRADING_END_TIME = time(15, 30) # NSE Equities ke liye standard time

# --- STRATEGY CONFIGURATION (from new config) ---
SELECTED_STRATEGIES = ["AlphaOneStrategy", "ApexStrategy", "NumeroUnoStrategy"]
STRATEGY_CAPITAL = {
    "AlphaOneStrategy": 100000,
    "ApexStrategy": 100000,
    "NumeroUnoStrategy": 100000,
}

# --- SYMBOL LISTS (Aapki live_config.py se) ---
NIFTY_50 = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "HINDUNILVR", "SBIN", "ITC", 
    # ... baki Nifty 50 stocks
]
BANKNIFTY_STOCKS = ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK"]


# --- FINAL SYMBOL CONFIGURATION (Flexible aur Powerful tarika) ---
# Yahan hum Nifty 50 list ka istemal kar rahe hain lekin har symbol ko alag timeframe de rahe hain.
SYMBOLS_TO_TRADE = []

# AlphaOne ke liye 15-min timeframe par Nifty 50 ke pehle 5 stocks
for symbol in NIFTY_50[:5]:
    SYMBOLS_TO_TRADE.append({'symbol': symbol, 'timeframe': 15})

# Apex aur NumeroUno ke liye 5-min timeframe par bank stocks
for symbol in BANKNIFTY_STOCKS:
    # Agar symbol pehle se list mein hai to dobara add na karein
    if not any(d['symbol'] == symbol for d in SYMBOLS_TO_TRADE):
        SYMBOLS_TO_TRADE.append({'symbol': symbol, 'timeframe': 5})

# --- EXECUTION SETTINGS (from new config) ---
MAIN_LOOP_SLEEP_SECONDS = 60
REQUIRED_INITIAL_CANDLES = 100