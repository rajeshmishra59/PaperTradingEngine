# connect_broker.py
import os, sys, logging
from pathlib import Path
import yaml
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

# ---------- Zerodha ----------
def connect_zerodha():
    try:
        from kiteconnect import KiteConnect
    except Exception:
        raise SystemExit("kiteconnect not installed. pip install kiteconnect")

    api_key = os.getenv("ZERODHA_API_KEY")
    access_token = os.getenv("ZERODHA_ACCESS_TOKEN")

    if not api_key or not access_token:
        log.error("Set ZERODHA_API_KEY and ZERODHA_ACCESS_TOKEN in .env (run login.py to generate token).")
        return False

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    try:
        _ = kite.margins("equity")   # cheap validation
        log.info("✅ Zerodha connected & validated.")
        return True
    except Exception as e:
        log.error(f"❌ Zerodha validation failed: {e}")
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

    # First, try to use the refresh token
    if refresh:
        try:
            log.info("🔁 Attempting AngelOne session via refresh token.")
            login_data = smart.generateSession(client, pw, refresh)
            # Handle case where login_data might be bytes, bytearray, or memoryview
            if isinstance(login_data, (bytes, bytearray, memoryview)):
                import json
                login_data = json.loads(bytes(login_data).decode('utf-8'))
            if login_data.get("status", False) is False:
                raise Exception(f"Refresh token failed: {login_data.get('message')}")
            log.info("✅ AngelOne session via refresh token successful.")
            login_successful = True
        except Exception as e:
            log.warning(f"⚠️ AngelOne refresh token failed: {e}. Trying TOTP...")

        # If refresh token failed or not available, try TOTP
        if not login_successful:
            try:
                assert totp_s is not None, "ANGELONE_TOTP_SECRET is not set"
                otp = pyotp.TOTP(totp_s).now()
                login_data = smart.generateSession(client, pw, otp)
                # Handle case where login_data might be bytes, bytearray, or memoryview
                if isinstance(login_data, (bytes, bytearray, memoryview)):
                    import json
                    login_data = json.loads(bytes(login_data).decode('utf-8'))
                if login_data.get("status", False) is False:
                    raise Exception(f"TOTP login failed: {login_data.get('message')}")
                log.info("🔐 AngelOne TOTP session created.")
                login_successful = True
            except Exception as e:
                log.error(f"❌ AngelOne TOTP login failed: {e}")
                return False

    # Save new refresh token if present
    try:
        new_refresh = getattr(smart, "refresh_token", None)
        if new_refresh and new_refresh != refresh:
            _save_env("ANGELONE_REFRESH_TOKEN", new_refresh)
            log.info("💾 Saved ANGELONE_REFRESH_TOKEN to .env")
    except Exception:
        pass

    # Validation: user profile fetch
    try:
        # Use the latest refresh token if available for validation
        current_refresh = getattr(smart, "refresh_token", refresh)
        _ = smart.getProfile(current_refresh)  # Use getProfile to validate the connection
        log.info("✅ AngelOne connected & validated.")
        return True
    except Exception as e:
        log.error(f"❌ AngelOne validation failed: {e}")
        return False

if __name__ == "__main__":
    broker = _load_selected_broker()
    log.info(f"Connecting broker from config.yml → {broker}")
    ok = connect_zerodha() if broker == "zerodha" else connect_angelone()
    sys.exit(0 if ok else 1)