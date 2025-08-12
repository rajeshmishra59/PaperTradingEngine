# File: broker_interface.py
# Unified Broker Interface: Zerodha (Kite) + Angel One (SmartAPI) for PAPER TRADING data.
# v3.0 – library + runnable CLI (runtime broker selection + connect validation)

import os
import sys
import logging
import requests  # Add this for Scrip Master download
import io        # Add this for CSV processing
import time
from datetime import datetime
from typing import Optional, Dict, Any, cast

import pandas as pd
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

# =========================
# Zerodha (KiteConnect)
# =========================
try:
    from kiteconnect import KiteConnect
except Exception:
    KiteConnect = None


class ZerodhaInterface:
    """
    Subset used by your engine:
      - set_access_token()
      - get_instruments()
      - get_historical_candles()
      - get_historical_data()              # compat shim (string intervals)
      - get_historical_data_by_interval()  # compat shim
      - get_ltp()
      - connect()  # lightweight validation
    """
    def __init__(self, api_key: str, api_secret: str, access_token: Optional[str] = None):
        if KiteConnect is None:
            raise ImportError("kiteconnect not installed. pip install kiteconnect")
        self.api_key = api_key
        self.api_secret = api_secret
        self.kite = KiteConnect(api_key=self.api_key)
        if access_token:
            self.set_access_token(access_token)

    def set_access_token(self, access_token: str):
        self.kite.set_access_token(access_token)
        logger.info("✅ Zerodha: Access token set.")

    def connect(self) -> bool:
        """
        Validate connectivity with a cheap API call.
        Returns True on success, False otherwise.
        """
        try:
            # margins is a tiny call; profile() also works
            _ = self.kite.margins(segment="equity")
            logger.info("✅ Zerodha: Connection validated.")
            return True
        except Exception as e:
            logger.error(f"❌ Zerodha: validation failed: {e}")
            return False

    def get_instruments(self, exchange: str = "NSE") -> pd.DataFrame:
        instruments = self.kite.instruments(exchange)
        return pd.DataFrame(instruments)

    def _resolve_token(self, instruments: pd.DataFrame, symbol: str) -> Optional[int]:
        row = instruments.loc[instruments['tradingsymbol'] == symbol]
        if not row.empty:
            return int(row.iloc[0]['instrument_token'])
        return None

    def get_historical_candles(self, symbol: str, interval: str, from_dt: datetime, to_dt: datetime) -> pd.DataFrame:
        """
        Kite intervals: 'minute','3minute','5minute','10minute','15minute','30minute','60minute','day'
        """
        instruments = self.get_instruments("NSE")
        token = self._resolve_token(instruments, symbol)
        if token is None:
            raise ValueError(f"Zerodha: instrument token not found for {symbol}")

        data = self.kite.historical_data(token, from_dt, to_dt, interval)
        df = pd.DataFrame(data)
        if not df.empty:
            df.rename(columns={"date": "datetime"}, inplace=True)
            df["datetime"] = pd.to_datetime(df["datetime"])
            df["symbol"] = symbol
        return df

    # --- compat shim: simple strings like 'minute' / '15minute'
    def get_historical_data(self, symbol: str, interval: str, from_date: datetime, to_date: datetime, **kwargs) -> pd.DataFrame:
        norm = (interval or "").lower()
        if norm in ("minute", "1minute", "1_minute", "1-min"):
            kite_interval = "minute"
        elif norm.endswith("minute"):
            kite_interval = norm                  # e.g., '15minute'
        elif norm in ("day", "1day", "daily"):
            kite_interval = "day"
        else:
            kite_interval = "minute"
        return self.get_historical_candles(symbol, kite_interval, from_date, to_date)

    # --- compat shim for older call sites
    def get_historical_data_by_interval(self, symbol: str, interval: str, from_date: datetime, to_date: datetime, **kwargs) -> pd.DataFrame:
        return self.get_historical_candles(symbol, interval, from_date, to_date)

    def get_ltp(self, symbol: str) -> float:
        q = cast(Dict[str, Dict[str, Any]], self.kite.ltp([f"NSE:{symbol}"]))
        return float(q[f"NSE:{symbol}"]["last_price"])


# =========================
# Angel One (SmartAPI)
# =========================
# Try both module names; some envs install SmartApi, some smartapi
try:
    from SmartApi import SmartConnect  # type: ignore
    import pyotp  # type: ignore
except Exception:
    try:
        from smartapi import SmartConnect  # type: ignore
        import pyotp  # type: ignore
    except Exception:
        SmartConnect = None
        pyotp = None


class AngelOneInterface:
    """
    Angel One SmartAPI wrapper for PAPER TRADING data.
    """
    INTERVAL_MAP = {
        1: "ONE_MINUTE",
        3: "THREE_MINUTE",
        5: "FIVE_MINUTE",
        10: "TEN_MINUTE",
        15: "FIFTEEN_MINUTE",
        30: "THIRTY_MINUTE",
        60: "ONE_HOUR",
        1440: "ONE_DAY",
    }

    def __init__(
        self,
        api_key: str,
        client_code: str,
        password: str,
        totp_secret: str,
        refresh_token: Optional[str] = None,
        instruments_csv: str = "angel_instruments.csv",
    ):
        if SmartConnect is None:
            raise ImportError("smartapi-python / SmartApi not installed. pip install smartapi-python pyotp")
        if pyotp is None:
            raise ImportError("pyotp not installed. pip install pyotp")

        self.api_key = api_key
        self.client_code = client_code
        self.password = password
        self.totp_secret = totp_secret
        self.refresh_token = refresh_token
        self.instruments_csv = instruments_csv

        self.smart: Optional[Any] = None
        self.instruments_df: Optional[pd.DataFrame] = None

        # Create session on init
        self.authenticate()

        self._last_hist_call = 0.0
        self._min_hist_gap = float(os.getenv("ANGELONE_RATE_SEC", "0.6"))  # seconds between calls

    def authenticate(self):
        if SmartConnect is None:
            raise ImportError("smartapi-python / SmartApi not installed. pip install smartapi-python pyotp")
        
        if pyotp is None:
            raise ImportError("pyotp not installed. pip install pyotp")
        
        # Always TOTP login on this build; save refresh for later APIs/WebSocket reuse
        self.smart = SmartConnect(api_key=self.api_key)  # type: ignore
        totp = pyotp.TOTP(self.totp_secret).now()
        data = self.smart.generateSession(self.client_code, self.password, totp)
        logger.info("✅ AngelOne: TOTP session created.")

        # Try to persist refresh token for later calls
        try:
            rtoken = None
            if isinstance(data, dict):
                rtoken = data.get("data", {}).get("refreshToken")
            if not rtoken:
                rtoken = getattr(self.smart, "refresh_token", None)
            if rtoken:
                self._save_env_value("ANGELONE_REFRESH_TOKEN", rtoken)
                logger.info("🔁 Saved ANGELONE_REFRESH_TOKEN to .env")
        except Exception:
            pass

    def connect(self) -> bool:
        """
        Validate connectivity with a tiny call.
        Returns True on success, False otherwise.
        """
        try:
            # Check if self.smart is None, re-authenticate if needed
            if self.smart is None:
                self.authenticate()
                if self.smart is None:  # Still None after authentication attempt
                    logger.error("❌ AngelOne: Failed to initialize Smart API client")
                    return False
                
            # getProfile is a lightweight validation endpoint (name may vary by version)
            if hasattr(self.smart, "getProfile"):
                _ = self.smart.getProfile(self.client_code)  # type: ignore
            else:
                # Fallback: instruments (slightly heavier but reliable)
                _ = self.smart.getInstruments("NSE")
            logger.info("✅ AngelOne: Connection validated.")
            return True
        except Exception as e:
            logger.error(f"❌ AngelOne: validation failed: {e}")
            return False

    def _save_env_value(self, key: str, value: str, env_path: str = ".env"):
        if not value:
            return
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
        found = False
        with open(env_path, "w", encoding="utf-8") as f:
            for line in lines:
                if line.startswith(f"{key}="):
                    f.write(f"{key}={value}\n")
                    found = True
                else:
                    f.write(line + "\n")
            if not found:
                f.write(f"{key}={value}\n")

    def get_instruments(self, exchange: str = "NSE") -> pd.DataFrame:
        if self.instruments_df is not None:
            # in-memory cache
            df = self.instruments_df
            if "exch_seg" in df.columns:
                return df[df["exch_seg"].str.contains(exchange, case=False, na=False)].copy()
            return df

        # disk cache?
        if os.path.exists(self.instruments_csv):
            df = pd.read_csv(self.instruments_csv, low_memory=False)  # <-- Added low_memory=False here
            self.instruments_df = df
            if "exch_seg" in df.columns:
                return df[df["exch_seg"].str.contains(exchange, case=False, na=False)].copy()
            return df

        # Try client method if present (some builds expose it), else fallback to public Scrip Master
        df = None
        if hasattr(self.smart, "getInstruments"):
            try:
                data = self.smart.getInstruments(exchange)  # type: ignore
                df = pd.DataFrame(data)
            except Exception as e:
                logger.warning(f"AngelOne getInstruments not available/failed: {e}. Falling back to Scrip Master.")

        if df is None or df.empty:
            # Public Scrip Master (JSON -> preferred; else CSV)
            json_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
            csv_url  = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.csv"
            try:
                r = requests.get(json_url, timeout=20)
                r.raise_for_status()
                df = pd.DataFrame(r.json())
            except Exception:
                r = requests.get(csv_url, timeout=20)
                r.raise_for_status()
                df = pd.read_csv(io.StringIO(r.text))

        if df is None or df.empty:
            raise ValueError("AngelOne instruments empty (Scrip Master load failed).")

        # Persist & cache
        try:
            df.to_csv(self.instruments_csv, index=False)
            logger.info(f"💾 Cached AngelOne instruments to {self.instruments_csv}")
        except Exception:
            pass

        self.instruments_df = df
        if "exch_seg" in df.columns:
            return df[df["exch_seg"].str.contains(exchange, case=False, na=False)].copy()
        return df

    def _resolve_token(self, instruments: pd.DataFrame, symbol: str, exchange: str = "NSE") -> Optional[str]:
        cands = instruments
        if "exch_seg" in cands.columns:
            cands = cands[cands["exch_seg"].str.contains(exchange, case=False, na=False)]
        for col in ["tradingsymbol", "symbol", "name"]:
            if col in cands.columns:
                row = cands.loc[cands[col] == symbol]
                if not row.empty:
                    token_col = "token" if "token" in row.columns else ("instrument_token" if "instrument_token" in row.columns else None)
                    if token_col:
                        return str(row.iloc[0][token_col])
        return None

    def get_historical_candles(self, symbol: str, interval: str, from_dt: datetime, to_dt: datetime, exchange: str = "NSE") -> pd.DataFrame:
        instruments = self.get_instruments(exchange)
        token = self._resolve_token(instruments, symbol, exchange=exchange)
        if token is None:
            raise ValueError(f"AngelOne: token not found for {symbol} ({exchange})")

        # Ensure SmartAPI client is initialized
        if self.smart is None:
            self.authenticate()
            if self.smart is None:  # Still None after authentication attempt
                raise RuntimeError("Failed to initialize SmartAPI client for getting historical data")

        params = {
            "exchange": exchange,
            "symboltoken": token,
            "interval": interval,
            "fromdate": from_dt.strftime("%Y-%m-%d %H:%M"),
            "todate": to_dt.strftime("%Y-%m-%d %H:%M"),
        }
        self._throttle_hist()
        resp = self._get_candles_with_retry(params)
        candles = resp.get("data", []) if resp else []
        cols = ["datetime", "open", "high", "low", "close", "volume"]
        df = pd.DataFrame(candles, columns=cols)
        if not df.empty:
            df["datetime"] = pd.to_datetime(df["datetime"])
            df["symbol"] = symbol
        return df

    def get_historical_data(self, symbol: str, interval: str, from_date: datetime, to_date: datetime, exchange: str = "NSE", **kwargs) -> pd.DataFrame:
        norm = (interval or "").lower()
        if norm in ("minute", "1minute", "1_minute", "1-min"):
            angel_interval = "ONE_MINUTE"
        elif norm in ("day", "1day", "daily"):
            angel_interval = "ONE_DAY"
        else:
            if norm.endswith("minute"):
                try:
                    n = int(norm.replace("minute", ""))
                except Exception:
                    n = 1
                angel_interval = {
                    1: "ONE_MINUTE",
                    3: "THREE_MINUTE",
                    5: "FIVE_MINUTE",
                    10: "TEN_MINUTE",
                    15: "FIFTEEN_MINUTE",
                    30: "THIRTY_MINUTE",
                    60: "ONE_HOUR",
                }.get(n, "FIFTEEN_MINUTE")
            else:
                angel_interval = "FIFTEEN_MINUTE"
        return self.get_historical_candles(symbol, angel_interval, from_date, to_date, exchange=exchange)

    def get_historical_data_by_interval(self, symbol: str, interval: str, from_date: datetime, to_date: datetime, exchange: str = "NSE", **kwargs) -> pd.DataFrame:
        return self.get_historical_candles(symbol, interval, from_date, to_date, exchange=exchange)

    def get_ltp(self, symbol: str, exchange: str = "NSE") -> float:
        # Ensure SmartAPI client is initialized
        if self.smart is None:
            self.authenticate()
            if self.smart is None:  # Still None after authentication attempt
                raise RuntimeError("Failed to initialize SmartAPI client for getting LTP")
                
        data = self.smart.ltpData(exchange, symbol, self._resolve_token(self.get_instruments(exchange), symbol, exchange))
        return float(data["data"]["ltp"])

    def _throttle_hist(self):
        gap = self._min_hist_gap
        now = time.perf_counter()
        wait = gap - (now - getattr(self, "_last_hist_call", 0.0))
        if wait > 0:
            time.sleep(wait)
        self._last_hist_call = time.perf_counter()

    def _get_candles_with_retry(self, params, retries: int = 5):
        # Ensure SmartAPI client is initialized
        if self.smart is None:
            self.authenticate()
            if self.smart is None:  # Still None after authentication attempt
                raise RuntimeError("Failed to initialize SmartAPI client for getting candle data")
                
        delay = 0.8
        last = None
        for _ in range(retries):
            try:
                return self.smart.getCandleData(params)
            except Exception as e:
                msg = str(e).lower()
                if "access rate" in msg or "rate" in msg or "429" in msg:
                    time.sleep(delay)
                    delay *= 1.6
                    last = e
                    continue
                raise
        if last:
            raise last


# =========================
# Broker Factory
# =========================

def get_broker_interface(config: Dict[str, Any]):
    """
    Creates a broker instance based on config['broker'].
    Supported: 'zerodha', 'angelone'
    """
    broker_name = (config.get("broker") or "zerodha").lower()

    if broker_name == "zerodha":
        z = config.get("zerodha", {})
        api_key = z.get("api_key") or os.getenv("ZERODHA_API_KEY")
        api_secret = z.get("api_secret") or os.getenv("ZERODHA_API_SECRET")
        access_token = z.get("access_token") or os.getenv("ZERODHA_ACCESS_TOKEN")
        if not (api_key and api_secret and access_token):
            raise ValueError("Missing Zerodha creds (api_key/api_secret/access_token).")
        return ZerodhaInterface(api_key=api_key, api_secret=api_secret, access_token=access_token)

    if broker_name == "angelone":
        a = config.get("angelone", {})
        api_key = a.get("api_key") or os.getenv("ANGELONE_API_KEY")
        client = a.get("client_code") or os.getenv("ANGELONE_CLIENT_CODE")
        pw = a.get("password") or os.getenv("ANGELONE_PASSWORD")
        totp_secret = a.get("totp_secret") or os.getenv("ANGELONE_TOTP_SECRET")
        refresh = a.get("refresh_token") or os.getenv("ANGELONE_REFRESH_TOKEN")
        if not (api_key and client and pw and totp_secret):
            raise ValueError("Missing Angel One creds (api_key/client_code/password/totp_secret).")
        return AngelOneInterface(api_key=api_key, client_code=client, password=pw, totp_secret=totp_secret, refresh_token=refresh)

    raise ValueError(f"Unsupported broker: {broker_name}")


# =========================
# CLI (Runtime Selection)
# =========================
def _normalize_choice(s: str) -> str:
    s = (s or "").strip().lower()
    if s in ("angel", "angelone", "angel-one", "smartapi"):
        return "angelone"
    if s in ("zerodha", "kite", "kiteconnect"):
        return "zerodha"
    return s

def _connect_interactive(choice: Optional[str] = None) -> int:
    # Lazy import to avoid circulars
    try:
        from config_loader import load_config
    except Exception:
        print("ERROR: config_loader not found. Ensure config_loader.py exists.")
        return 2

    CONFIG = load_config()

    if not choice:
        # Prompt user
        user = input("Select broker [zerodha/angelone]: ").strip()
        choice = _normalize_choice(user)

    choice = _normalize_choice(choice)
    if choice not in ("zerodha", "angelone"):
        print(f"Unsupported choice: {choice!r}. Use 'zerodha' or 'angelone'.")
        return 2

    # Override config choice at runtime
    CONFIG["broker"] = choice

    print(f"\n➡️  Initializing broker: {choice} ...")
    try:
        broker = get_broker_interface(CONFIG)
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return 1

    # Validate connectivity
    try:
        ok = False
        if hasattr(broker, "connect"):
            ok = bool(broker.connect())
        else:
            # Fallback: a tiny call
            if choice == "zerodha":
                ok = bool(len(broker.get_instruments("NSE")) >= 0)
            else:
                ok = bool(len(broker.get_instruments("NSE")) >= 0)
        if ok:
            print(f"✅ Connected to broker: {broker.__class__.__name__}")
            return 0
        else:
            print(f"❌ Connection check failed for {broker.__class__.__name__}")
            return 1
    except Exception as e:
        print(f"❌ Connectivity error: {e}")
        return 1


if __name__ == "__main__":
    # Usage:
    #   python broker_interface.py
    #   python broker_interface.py --broker angelone
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    parser = argparse.ArgumentParser(description="Select and connect to a broker (Zerodha/Angel One).")
    parser.add_argument("--broker", "-b", dest="broker", default=None, help="zerodha or angelone")
    args = parser.parse_args()

    sys.exit(_connect_interactive(args.broker))
