#!/bin/bash
# Auto Broker Connection Script
# This script will automatically reconnect broker on system startup

TRADING_DIR="/home/ubuntu/PaperTradingV1.3"
LOG_FILE="$TRADING_DIR/logs/broker_connection.log"

# Create log directory
mkdir -p "$TRADING_DIR/logs"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Change to trading directory
cd "$TRADING_DIR"

log "🔗 Starting Automatic Broker Connection Process..."

# Check which broker is configured
BROKER=$(python3 -c "
import yaml
with open('automation/configs/config.yml', 'r') as f:
    config = yaml.safe_load(f)
print(config.get('broker', 'zerodha').lower())
" 2>/dev/null || echo "zerodha")

log "📊 Detected broker: $BROKER"

# Try automatic connection based on broker type
if [ "$BROKER" = "zerodha" ]; then
    log "🔑 Attempting Zerodha connection..."
    
    # Check if access token exists and is not expired
    ZERODHA_TOKEN=$(grep "ZERODHA_ACCESS_TOKEN" .env | cut -d'=' -f2 2>/dev/null || echo "")
    
    if [ -n "$ZERODHA_TOKEN" ]; then
        log "✅ Found existing Zerodha access token"
        
        # Test the token by running a quick broker check
        python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

try:
    from broker_interface import get_broker_interface
    from config_loader import CONFIG
    
    broker = get_broker_interface(CONFIG)
    # Simple validation - if this works, token is valid
    print('✅ Zerodha connection validated')
    exit(0)
except Exception as e:
    print(f'❌ Zerodha connection failed: {e}')
    exit(1)
" >> "$LOG_FILE" 2>&1
        
        if [ $? -eq 0 ]; then
            log "✅ Zerodha connection validated successfully"
            echo "ZERODHA_CONNECTED" > "$TRADING_DIR/broker_status.txt"
        else
            log "⚠️ Zerodha token validation failed - needs refresh"
            echo "ZERODHA_TOKEN_EXPIRED" > "$TRADING_DIR/broker_status.txt"
        fi
    else
        log "❌ No Zerodha access token found"
        echo "ZERODHA_NO_TOKEN" > "$TRADING_DIR/broker_status.txt"
    fi

elif [ "$BROKER" = "angelone" ]; then
    log "🔑 Attempting Angel One connection..."
    
    # Angel One uses TOTP-based auto login
    python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

try:
    from SmartApi import SmartConnect
    import pyotp
    
    api_key = os.getenv('ANGELONE_API_KEY')
    client = os.getenv('ANGELONE_CLIENT_CODE')
    password = os.getenv('ANGELONE_PASSWORD')
    totp_secret = os.getenv('ANGELONE_TOTP_SECRET')
    
    if not all([api_key, client, password, totp_secret]):
        print('❌ Angel One credentials missing')
        exit(1)
    
    smart = SmartConnect(api_key=api_key)
    totp = pyotp.TOTP(totp_secret).now()
    
    login_data = smart.generateSession(client, password, totp)
    
    if isinstance(login_data, (bytes, bytearray, memoryview)):
        import json
        login_data = json.loads(bytes(login_data).decode('utf-8'))
    
    if login_data.get('status', False):
        print('✅ Angel One connection successful')
        exit(0)
    else:
        print(f'❌ Angel One login failed: {login_data.get(\"message\", \"Unknown error\")}')
        exit(1)
        
except Exception as e:
    print(f'❌ Angel One connection error: {e}')
    exit(1)
" >> "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        log "✅ Angel One connection successful"
        echo "ANGELONE_CONNECTED" > "$TRADING_DIR/broker_status.txt"
    else
        log "❌ Angel One connection failed"
        echo "ANGELONE_FAILED" > "$TRADING_DIR/broker_status.txt"
    fi
fi

# Final status
BROKER_STATUS=$(cat "$TRADING_DIR/broker_status.txt" 2>/dev/null || echo "UNKNOWN")
log "📊 Final Broker Status: $BROKER_STATUS"

# Exit with appropriate code
if [[ "$BROKER_STATUS" == *"CONNECTED"* ]]; then
    log "🎉 Broker connection completed successfully!"
    exit 0
else
    log "⚠️ Broker connection needs attention"
    exit 1
fi
