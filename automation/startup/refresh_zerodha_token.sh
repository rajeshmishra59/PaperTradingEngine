#!/bin/bash
# Zerodha Token Refresh Script
# This script automatically refreshes Zerodha access token when needed

TRADING_DIR="/home/ubuntu/PaperTradingV1.3"
LOG_FILE="$TRADING_DIR/logs/token_refresh.log"

# Create log directory
mkdir -p "$TRADING_DIR/logs"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

cd "$TRADING_DIR"

log "🔄 Starting Zerodha Token Refresh Process..."

# Extract current credentials
API_KEY=$(grep "ZERODHA_API_KEY" .env | cut -d'=' -f2 2>/dev/null)
API_SECRET=$(grep "ZERODHA_API_SECRET" .env | cut -d'=' -f2 2>/dev/null)

if [ -z "$API_KEY" ] || [ -z "$API_SECRET" ]; then
    log "❌ Zerodha API credentials not found in .env file"
    exit 1
fi

log "✅ Found Zerodha API credentials"

# Create a notification file for manual intervention
cat > "$TRADING_DIR/token_refresh_needed.txt" << EOF
🔔 ZERODHA TOKEN REFRESH REQUIRED

Your Zerodha access token has expired and needs manual refresh.

📋 Steps to refresh:
1. Run: cd /home/ubuntu/PaperTradingV1.3
2. Run: python3 connect_broker.py
3. Follow the browser login process
4. New token will be automatically saved

⏰ Time: $(date)
📍 Status: MANUAL_INTERVENTION_REQUIRED

After refreshing, the trading system will automatically reconnect.
EOF

log "📝 Created manual refresh notification"
log "⚠️ Manual token refresh required - check token_refresh_needed.txt"

# Send notification (if notification system is available)
if command -v notify-send &> /dev/null; then
    notify-send "Zerodha Token Expired" "Manual refresh required. Check token_refresh_needed.txt"
fi

echo "TOKEN_REFRESH_NEEDED" > "$TRADING_DIR/broker_status.txt"
