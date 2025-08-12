# data_router.py
from datetime import datetime
import pandas as pd

INDEX_SYMBOLS = {"NIFTY50", "NIFTY_50", "^NSEI"}  # add more if needed

def is_index_symbol(symbol: str) -> bool:
    s = (symbol or "").strip().upper()
    return s in INDEX_SYMBOLS or s.startswith("^")

def fetch_from_yahoo(symbol: str, minutes: int, start: datetime, end: datetime) -> pd.DataFrame:
    import yfinance as yf
    tf = f"{minutes}m" if minutes < 60 else "1d"
    yf_symbol = "^NSEI" if symbol.upper() in {"NIFTY50", "NIFTY_50"} else symbol
    df = yf.download(yf_symbol, interval=tf, start=start, end=end, progress=False)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
    df = df.reset_index().rename(columns={"Datetime":"datetime","Date":"datetime"})
    df["symbol"] = symbol
    return df[["datetime","open","high","low","close","volume","symbol"]]

def _to_interval_for(broker, minutes: int) -> str:
    try:
        from broker_interface import ZerodhaInterface, AngelOneInterface
        if isinstance(broker, ZerodhaInterface):
            return f"{minutes}minute" if minutes < 60 else "day"
        if isinstance(broker, AngelOneInterface):
            return AngelOneInterface.INTERVAL_MAP.get(minutes, "FIFTEEN_MINUTE")
    except Exception:
        pass
    return "minute" if minutes < 60 else "day"

def get_historical(broker, symbol: str, minutes: int, start: datetime, end: datetime) -> pd.DataFrame:
    """Route index to Yahoo; others to active broker."""
    if is_index_symbol(symbol):
        return fetch_from_yahoo(symbol, minutes, start, end)
    interval = _to_interval_for(broker, minutes)
    return broker.get_historical_data(symbol, interval, start, end)
