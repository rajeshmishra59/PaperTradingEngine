# File: broker_interface.py
# Inspired by your zerodha_data_collector.py, with self-healing instrument file logic.

import os
import logging
import pandas as pd
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ZerodhaInterface:
    def __init__(self, api_key: str, api_secret: str, access_token: str = None):
        """Initializes the Zerodha KiteConnect interface."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.kite = KiteConnect(api_key=self.api_key)
        self.instrument_df = None
        self.instrument_map = {}

        if access_token:
            self.set_access_token(access_token)
        
        # Atma-nirbhar instrument file logic
        self._initialize_instruments()

    def set_access_token(self, access_token: str):
        """Sets the access token for the Kite session."""
        try:
            self.kite.set_access_token(access_token)
            logger.info("✅ Zerodha Access Token set successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to set access token: {e}")
            raise

    def _initialize_instruments(self, exchange="NSE"):
        """
        Loads instruments from a local CSV file. If the file doesn't exist,
        it fetches them from Zerodha and creates the file.
        """
        instrument_file = "instruments.csv"
        try:
            if os.path.exists(instrument_file):
                self.instrument_df = pd.read_csv(instrument_file)
                logger.info(f"✅ Loaded instruments from local '{instrument_file}'.")
            else:
                logger.warning(f"'{instrument_file}' not found. Fetching from Zerodha...")
                # Fetching requires a valid session
                if not self.kite.access_token:
                    logger.error("❌ Cannot fetch instruments without an access token.")
                    return
                
                instruments = self.kite.instruments(exchange)
                self.instrument_df = pd.DataFrame(instruments)
                self.instrument_df.to_csv(instrument_file, index=False)
                logger.info(f"✅ Instruments fetched and saved to '{instrument_file}'.")

            # Create a mapping for faster lookups
            nse_df = self.instrument_df[self.instrument_df["exchange"] == exchange]
            self.instrument_map = dict(zip(nse_df["tradingsymbol"], nse_df["instrument_token"]))

        except Exception as e:
            logger.error(f"❌ Failed to initialize instruments: {e}")
            self.instrument_df = pd.DataFrame()

    def get_instrument_token(self, symbol: str) -> int:
        """Finds the instrument token for a given trading symbol."""
        token = self.instrument_map.get(symbol.upper())
        if not token:
            logger.error(f"❌ Instrument token not found for {symbol}.")
        return token

    def get_historical_data(self, symbol: str, interval: str, from_date: datetime, to_date: datetime) -> pd.DataFrame:
        """
        Fetches historical data using the robust chunking method.
        """
        instrument_token = self.get_instrument_token(symbol)
        if not instrument_token:
            return pd.DataFrame()

        delta_map = {
            "minute": timedelta(minutes=400), "3minute": timedelta(minutes=3*400),
            "5minute": timedelta(minutes=5*400), "10minute": timedelta(minutes=10*400),
            "15minute": timedelta(minutes=15*400), "day": timedelta(days=400),
        }
        delta = delta_map.get(interval, timedelta(minutes=400))
        chunks = []
        cur_from = from_date
        
        while cur_from < to_date:
            cur_to = min(cur_from + delta, to_date)
            try:
                data = self.kite.historical_data(instrument_token, cur_from, cur_to, interval)
                if data:
                    chunks.append(pd.DataFrame(data))
                else:
                    break # No more data
            except Exception as e:
                logger.error(f"❌ Error fetching data chunk for {symbol}: {e}")
                break
            cur_from = cur_to
        
        if not chunks:
            return pd.DataFrame()
            
        df = pd.concat(chunks, ignore_index=True)
        df.rename(columns={'date': 'timestamp'}, inplace=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        return df

# --- CLI Token Generator (Aapke code se) ---
def generate_token_cli():
    """Interactive CLI to generate and save a new access token."""
    load_dotenv()
    api_key = os.getenv("ZERODHA_API_KEY")
    api_secret = os.getenv("ZERODHA_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ ZERODHA_API_KEY or ZERODHA_API_SECRET not found in .env file.")
        return

    kite = KiteConnect(api_key=api_key)
    print("\n🔗 Visit and login via this URL:\n")
    print(kite.login_url())
    
    request_token = input("\nPaste the request_token from the redirected URL: ").strip()
    
    try:
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        print(f"✅ New Access Token: {access_token}")

        # Save to .env file automatically
        env_path = ".env"
        lines = []
        token_updated = False
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()
        
        with open(env_path, "w") as f:
            for line in lines:
                if line.startswith("ZERODHA_ACCESS_TOKEN="):
                    f.write(f"ZERODHA_ACCESS_TOKEN={access_token}\n")
                    token_updated = True
                else:
                    f.write(line)
            if not token_updated:
                 f.write(f"\nZERODHA_ACCESS_TOKEN={access_token}\n")

        print(f"✅ Access token automatically saved to '{env_path}'.")

    except Exception as e:
        print(f"❌ Error during token generation: {e}")

if __name__ == "__main__":
    generate_token_cli()