# connect_broker.py
import os, sys, logging
from pathlib import Path
import yaml
import webbrowser
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("connect_broker")
load_dotenv()

CFG = Path("config.yml")
ENV = Path(".env")

def _save_env(key: str, val: str):
    if not val: 
        return
    lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    out, seen = [], False
    for line in lines:
        if line.startswith(f"{key}="):
            out.append(f"{key}={val}")
            seen = True
        else:
            out.append(line)
    if not seen:
        out.append(f"{key}={val}")
    ENV.write_text("\n".join(out) + "\n", encoding="utf-8")

def _load_selected_broker():
    cfg = yaml.safe_load(CFG.read_text(encoding="utf-8"))
    return (cfg.get("broker") or "zerodha").lower()

def _prompt_for_login(broker_name):
    """Ask user if they want to generate new login credentials"""
    print(f"\n❌ {broker_name.title()} connection failed!")
    print("This might be due to expired or invalid credentials.")
    choice = input(f"Would you like to generate new {broker_name.title()} login credentials? (y/n): ").strip().lower()
    return choice in ['y', 'yes']

# ---------- Zerodha Login ----------
def login_zerodha():
    """Generate Zerodha access token"""
    try:
        from kiteconnect import KiteConnect
    except ImportError:
        log.error("kiteconnect not installed. Please run: pip install kiteconnect")
        return False

    api_key = os.getenv("ZERODHA_API_KEY")
    api_secret = os.getenv("ZERODHA_API_SECRET")
    
    if not api_key or not api_secret:
        log.error("ZERODHA_API_KEY or ZERODHA_API_SECRET not found in .env file")
        log.info("Please add these to your .env file first:")
        log.info("ZERODHA_API_KEY=your_api_key")
        log.info("ZERODHA_API_SECRET=your_api_secret")
        return False
    
    kite = KiteConnect(api_key=api_key)
    
    # Generate login URL
    login_url = kite.login_url()
    log.info(f"🔗 Zerodha Login URL: {login_url}")
    log.info("\n📋 Steps to generate Zerodha access token:")
    log.info("1. Copy the above URL and open it in your browser")
    log.info("2. Login with your Zerodha credentials")
    log.info("3. After successful login, you'll be redirected to a URL with 'request_token' parameter")
    log.info("4. Copy the 'request_token' value from the URL and paste it below")
    
    # Try to open the URL automatically
    try:
        webbrowser.open(login_url)
        log.info("✅ Login URL opened in your default browser")
    except:
        log.info("⚠️ Could not open browser automatically. Please copy the URL manually.")
    
    print("\n" + "="*60)
    request_token = input("Enter the request_token from the redirected URL: ").strip()
    
    if not request_token:
        log.error("No request token provided")
        return False
    
    try:
        # Generate session
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        
        log.info(f"\n✅ Zerodha access token generated successfully!")
        log.info(f"🔑 Access Token: {access_token}")
        
        # Save to .env file
        _save_env("ZERODHA_ACCESS_TOKEN", access_token)
        log.info("✅ Access token saved to .env file")
        return True
            
    except Exception as e:
        log.error(f"Failed to generate Zerodha access token: {e}")
        return False

# ---------- Angel One Login ----------
def login_angelone():
    """Generate Angel One session and refresh token"""
    try:
        from SmartApi import SmartConnect  # type: ignore
    except ImportError:
        try:
            from smartapi import SmartConnect  # type: ignore
        except ImportError:
            log.error("SmartAPI not installed. Please run: pip install smartapi-python pyotp")
            return False
    
    try:
        import pyotp
    except ImportError:
        log.error("pyotp not installed. Please run: pip install pyotp")
        return False

    api_key = os.getenv("ANGELONE_API_KEY")
    client = os.getenv("ANGELONE_CLIENT_CODE")
    password = os.getenv("ANGELONE_PASSWORD")
    totp_secret = os.getenv("ANGELONE_TOTP_SECRET")
    
    if not all([api_key, client, password, totp_secret]):
        log.error("Angel One credentials not found in .env file")
        log.info("Please add these to your .env file:")
        log.info("ANGELONE_API_KEY=your_api_key")
        log.info("ANGELONE_CLIENT_CODE=your_client_code")
        log.info("ANGELONE_PASSWORD=your_mpin")
        log.info("ANGELONE_TOTP_SECRET=your_totp_secret")
        return False
    
    smart = SmartConnect(api_key=api_key)
    
    try:
        log.info("🔑 Attempting Angel One login via TOTP...")
        totp = pyotp.TOTP(totp_secret).now()
        log.info(f"Generated TOTP: {totp}")
        
        login_data = smart.generateSession(client, password, totp)
        
        # Handle different response types
        if isinstance(login_data, (bytes, bytearray, memoryview)):
            import json
            login_data = json.loads(bytes(login_data).decode('utf-8'))
        
        if not login_data.get("status", False):
            raise Exception(f"Login failed: {login_data.get('message', 'Unknown error')}")
        
        # Extract tokens
        data = login_data.get("data", {})
        refresh_token = data.get("refreshToken")
        jwt_token = data.get("jwtToken")
        
        log.info("✅ Angel One login successful!")
        
        if refresh_token:
            _save_env("ANGELONE_REFRESH_TOKEN", refresh_token)
            log.info("✅ Refresh token saved to .env file")
        
        if jwt_token:
            log.info(f"🔑 JWT Token: {jwt_token[:50]}...")
            
        # Test the connection
        try:
            profile = smart.getProfile(jwt_token)
            log.info(f"✅ Connection validated. User: {profile.get('data', {}).get('name', 'Unknown')}")
        except Exception as e:
            log.info(f"⚠️ Connection validation failed: {e}")
            
        return True
        
    except Exception as e:
        log.error(f"Angel One login failed: {e}")
        return False

# ---------- Zerodha ----------
def connect_zerodha():
    try:
        from kiteconnect import KiteConnect
    except Exception:
        raise SystemExit("kiteconnect not installed. pip install kiteconnect")

    api_key = os.getenv("ZERODHA_API_KEY")
    access_token = os.getenv("ZERODHA_ACCESS_TOKEN")

    if not api_key or not access_token:
        log.error("Set ZERODHA_API_KEY and ZERODHA_ACCESS_TOKEN in .env")
        
        # Offer to generate new token
        if _prompt_for_login("zerodha"):
            if login_zerodha():
                # Reload the access token and try again
                load_dotenv()
                access_token = os.getenv("ZERODHA_ACCESS_TOKEN")
                if not access_token:
                    log.error("Failed to get new access token")
                    return False
            else:
                return False
        else:
            return False

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    try:
        _ = kite.margins("equity")   # cheap validation
        log.info("✅ Zerodha connected & validated.")
        return True
    except Exception as e:
        log.error(f"❌ Zerodha validation failed: {e}")
        
        # Offer to generate new token on validation failure
        if _prompt_for_login("zerodha"):
            if login_zerodha():
                # Try connecting again with new token
                load_dotenv()
                new_access_token = os.getenv("ZERODHA_ACCESS_TOKEN")
                if new_access_token:
                    kite.set_access_token(new_access_token)
                    try:
                        _ = kite.margins("equity")
                        log.info("✅ Zerodha connected & validated with new token.")
                        return True
                    except Exception as e2:
                        log.error(f"❌ Still failed with new token: {e2}")
                        return False
        return False

# ---------- Angel One ----------
def connect_angelone():
    try:
        from SmartApi import SmartConnect  # type: ignore
    except Exception as e1:
        try:
            from smartapi import SmartConnect  # type: ignore
        except Exception as e2:
            raise SystemExit(
                "SmartAPI import failed. Install: pip install smartapi-python pyotp\n"
                f" - SmartApi error: {e1}\n - smartapi error: {e2}\n"
            )
    import pyotp  # ensure installed

    api_key = os.getenv("ANGELONE_API_KEY")
    client  = os.getenv("ANGELONE_CLIENT_CODE")
    pw      = os.getenv("ANGELONE_PASSWORD")
    totp_s  = os.getenv("ANGELONE_TOTP_SECRET")
    refresh = os.getenv("ANGELONE_REFRESH_TOKEN")

    if not all([api_key, client, pw, totp_s]):
        log.error("Set ANGELONE_API_KEY, ANGELONE_CLIENT_CODE, ANGELONE_PASSWORD, ANGELONE_TOTP_SECRET in .env")
        return False

    smart = SmartConnect(api_key=api_key)
    login_successful = False

    # Try TOTP login directly (refresh token approach was problematic)
    try:
        log.info("🔑 Attempting AngelOne login via TOTP.")
        totp = pyotp.TOTP(totp_s).now()
        login_data = smart.generateSession(client, pw, totp)
        if isinstance(login_data, (bytes, bytearray, memoryview)):
            import json
            login_data = json.loads(bytes(login_data).decode('utf-8'))
        if login_data.get("status", False) is False:
            raise Exception(f"Login failed: {login_data.get('message')}")
        
        # Save the new refresh token
        new_refresh_token = login_data.get("data", {}).get("refreshToken")
        if new_refresh_token:
            _save_env("ANGELONE_REFRESH_TOKEN", new_refresh_token)
            log.info("✅ AngelOne login successful & refresh token saved.")
        else:
            log.info("✅ AngelOne login successful.")

        login_successful = True
    except Exception as e:
        log.error(f"❌ AngelOne login via TOTP failed: {e}")
        
        # Offer to generate new credentials
        if _prompt_for_login("angelone"):
            if login_angelone():
                login_successful = True
            else:
                return False
        else:
            return False

    if not login_successful:
        return False

    try:
        # cheap validation
        _ = smart.getProfile(login_data.get("data", {}).get("jwtToken"))
        log.info("✅ AngelOne connected & validated.")
        return True
    except Exception as e:
        log.error(f"❌ AngelOne validation failed: {e}")
        return False

# ---------- Main ----------
def main():
    broker = _load_selected_broker()
    log.info(f"Connecting to {broker.title()}...")
    
    if broker == "zerodha":
        success = connect_zerodha()
    elif broker == "angelone":
        success = connect_angelone()
    else:
        log.error(f"Unknown broker: {broker}")
        return False
    
    if success:
        log.info(f"🎉 {broker.title()} connection successful!")
        return True
    else:
        log.error(f"❌ {broker.title()} connection failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)