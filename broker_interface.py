# File: broker_interface.py
# Final Production Version 1.5 (with interactive login)

import os
import logging
import pandas as pd
from datetime import datetime
from kiteconnect import KiteConnect
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ZerodhaInterface:
    # (The class code is the same as before, no changes needed here)
    def __init__(self, api_key: str, api_secret: str, access_token: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.kite = KiteConnect(api_key=self.api_key)
        self.instrument_df = None
        self.instrument_map = {}

        if access_token:
            self.set_access_token(access_token)
        
        self._initialize_instruments()

    def set_access_token(self, access_token: str):
        try:
            self.kite.set_access_token(access_token)
            logger.info("✅ Zerodha Access Token set successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to set access token: {e}")
            raise

    def _initialize_instruments(self, exchange="NSE"):
        instrument_file = "instruments.csv"
        try:
            if os.path.exists(instrument_file):
                self.instrument_df = pd.read_csv(instrument_file)
            else:
                if not self.kite.access_token:
                    logger.error("❌ Cannot fetch instruments without an access token.")
                    return
                instruments = self.kite.instruments(exchange)
                self.instrument_df = pd.DataFrame(instruments)
                self.instrument_df.to_csv(instrument_file, index=False)
                logger.info(f"✅ Instruments fetched and saved to '{instrument_file}'.")

            nse_df = self.instrument_df[self.instrument_df["exchange"] == exchange]
            self.instrument_map = dict(zip(nse_df["tradingsymbol"], nse_df["instrument_token"]))
            logger.info(f"✅ Loaded {len(self.instrument_map)} NSE instruments.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize instruments: {e}")
            self.instrument_df = pd.DataFrame()

    def get_instrument_token(self, symbol: str) -> int:
        token = self.instrument_map.get(symbol.upper())
        if not token:
            logger.error(f"❌ Instrument token not found for {symbol}.")
        return token

    def get_historical_data(self, symbol: str, interval: str, from_date: datetime, to_date: datetime) -> pd.DataFrame:
        instrument_token = self.get_instrument_token(symbol)
        if not instrument_token:
            return pd.DataFrame()
        
        try:
            records = self.kite.historical_data(instrument_token=instrument_token, from_date=from_date, to_date=to_date, interval=interval)
            if not records:
                logger.warning(f"No historical data received for {symbol} for the given period.")
                return pd.DataFrame()
            df = pd.DataFrame(records)
            df.rename(columns={'date': 'timestamp'}, inplace=True)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            if df['timestamp'].dt.tz is None:
                df['timestamp'] = df['timestamp'].dt.tz_localize('Asia/Kolkata')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logger.error(f"❌ API Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

# --- THIS IS THE MISSING PART ---
if __name__ == "__main__":
    """
    This block runs ONLY when you execute `python broker_interface.py`
    It guides you through the interactive login process.
    """
    try:
        load_dotenv()
        api_key = os.getenv("ZERODHA_API_KEY")
        api_secret = os.getenv("ZERODHA_API_SECRET")
        
        if not api_key or not api_secret:
            print("❌ ERROR: ZERODHA_API_KEY or ZERODHA_API_SECRET not found in your .env file.")
        else:
            kite = KiteConnect(api_key=api_key)
            
            print("--- Zerodha Access Token Generation ---")
            print("\nStep 1: A login URL will be generated. Copy and paste it into your browser.")
            input("Press Enter to generate the URL...")
            
            print(f"\n🔗 Login URL: {kite.login_url()}")
            
            request_token = input("\nStep 2: After logging in, you will be redirected. Copy the 'request_token' from the new URL and paste it here: ").strip()
            
            if request_token:
                data = kite.generate_session(request_token, api_secret=api_secret)
                access_token = data["access_token"]
                
                print(f"\n✅ SUCCESS! New Access Token: {access_token}")
                
                # Save to .env file automatically
                env_path = ".env"
                if os.path.exists(env_path):
                    with open(env_path, "r") as f:
                        lines = f.readlines()
                    
                    with open(env_path, "w") as f:
                        token_updated = False
                        for line in lines:
                            if line.startswith("ZERODHA_ACCESS_TOKEN="):
                                f.write(f"ZERODHA_ACCESS_TOKEN={access_token}\n")
                                token_updated = True
                            else:
                                f.write(line)
                        if not token_updated:
                             f.write(f"\nZERODHA_ACCESS_TOKEN={access_token}\n")
                    print(f"✅ Access token automatically saved to your '{env_path}' file.")
                else:
                    print(f"⚠️ Could not find .env file. Please add this line manually: ZERODHA_ACCESS_TOKEN={access_token}")
            else:
                print("❌ ERROR: No request token provided. Process cancelled.")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")