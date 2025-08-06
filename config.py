# File: config.py (Final Centralized Version)

from datetime import time
import os
from dotenv import load_dotenv

# --- API KEY LOADING ---
# .env file se sabhi zaroori credentials yahin load honge
load_dotenv() 
ZERODHA_API_KEY = os.getenv("ZERODHA_API_KEY")
ZERODHA_API_SECRET = os.getenv("ZERODHA_API_SECRET") # <-- YAHAN PAR SECRET KEY KO ADD KIYA GAYA HAI
ZERODHA_ACCESS_TOKEN = os.getenv("ZERODHA_ACCESS_TOKEN")

# --- TRADING SESSION ---
TRADING_START_TIME = time(9, 15)
TRADING_END_TIME = time(15, 35) # NSE Equities ke liye standard time

# --- MASTER SYMBOL LISTS ---
NIFTY_50 = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "HINDUNILVR", "SBIN", "ITC", "BHARTIARTL", "KOTAKBANK",
    "LT", "ASIANPAINT", "HCLTECH", "BAJFINANCE", "MARUTI", "AXISBANK", "ULTRACEMCO", "NESTLEIND", "SUNPHARMA", "TITAN",
    "WIPRO", "TECHM", "POWERGRID", "COALINDIA", "NTPC", "GRASIM", "TATAMOTORS", "JSWSTEEL", "ADANIENT", "ADANIPORTS",
    "DIVISLAB", "ONGC", "HINDALCO", "SBILIFE", "BAJAJFINSV", "BRITANNIA", "HEROMOTOCO", "CIPLA", "EICHERMOT", "BPCL",
    "UPL", "INDUSINDBK", "APOLLOHOSP", "HDFCLIFE", "BAJAJ-AUTO", "TATASTEEL", "SHREECEM", "DRREDDY", "M&M", "IOC"
]

NIFTY_NEXT_50 = [
    "AMBUJACEM", "AUROPHARMA", "BANKBARODA", "BERGEPAINT", "CANBK", "CHOLAFIN", "DABUR", "DLF", "GAIL",
    "GODREJCP", "ICICIGI", "ICICIPRULI", "IDFCFIRSTB", "IGL", "INDIGO", "MUTHOOTFIN", "NAUKRI", "PIDILITIND",
    "PNB", "RECLTD", "SAIL", "SRF", "TORNTPHARM", "TVSMOTOR", "UBL", "VEDL", "VOLTAS", "HAVELLS", "PEL", "PAGEIND", "COLPAL", "GLAND", "MPHASIS", "PETRONET", "HINDPETRO", "TRENT", "BEL",
    "CUMMINSIND", "ABBOTINDIA", "SBICARD", "INDUSTOWER", "BIOCON", "YESBANK", "BOSCHLTD", "CONCOR", "NMDC"
]

# --- STRATEGY & SYMBOL CONFIGURATION ---
STRATEGY_CONFIG = {
    "AlphaOneStrategy": {
        "timeframe": 15,
        "symbols": NIFTY_50,
        "capital": 100000
    },
    "ApexStrategy": {
        "timeframe": 5,
        "symbols": NIFTY_50,
        "capital": 100000
    },
    "NumeroUnoStrategy": {
        "timeframe": 5,
        "symbols": NIFTY_50,
        "capital": 100000
    },
    "SankhyaEkStrategy": {
        "timeframe": 5,
        "symbols": NIFTY_50,
        "capital": 100000
    },
    "TestStrategy": {
        "timeframe": 1,
        "symbols": NIFTY_50,
        "capital": 100000
    }
}

# --- EXECUTION SETTINGS ---
MAIN_LOOP_SLEEP_SECONDS = 30
REQUIRED_INITIAL_CANDLES = 100
