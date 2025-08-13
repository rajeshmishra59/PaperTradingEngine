#!/bin/bash
# Simple Auto Trading Startup Script
# This will automatically start trading system at 9:00 AM on weekdays

TRADING_DIR="/home/ubuntu/PaperTradingV1.3"
LOG_FILE="$TRADING_DIR/logs/auto_startup_simple.log"

# Create log directory
mkdir -p "$TRADING_DIR/logs"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if it's a weekday
DAY=$(date +%u)  # 1=Monday, 7=Sunday
if [ "$DAY" -gt 5 ]; then
    log "🚫 Weekend - Trading system will not start"
    exit 0
fi

# Check current time in IST (Indian Standard Time)
CURRENT_HOUR=$(TZ=Asia/Kolkata date +%H)
CURRENT_MIN=$(TZ=Asia/Kolkata date +%M)
CURRENT_TIME="$CURRENT_HOUR:$CURRENT_MIN"

# Market hours: 9:00 AM to 3:30 PM IST
if [ "$CURRENT_HOUR" -lt 9 ] || [ "$CURRENT_HOUR" -gt 15 ]; then
    log "🕒 Outside market hours IST ($CURRENT_TIME) - No action needed"
    exit 0
fi

if [ "$CURRENT_HOUR" -eq 15 ] && [ "$CURRENT_MIN" -gt 30 ]; then
    log "🕒 Market closed IST ($CURRENT_TIME) - No action needed"
    exit 0
fi

# Check if already running
if pgrep -f "python.*main_papertrader" > /dev/null; then
    log "ℹ️ Trading system already running - No action needed"
    exit 0
fi

# Start the trading system
log "🚀 Starting Paper Trading System at $CURRENT_TIME"

# Start background monitor first
if ! pgrep -f "background_monitor.sh" > /dev/null; then
    log "🔍 Starting background system monitor..."
    cd "$TRADING_DIR"
    nohup ./background_monitor.sh > /dev/null 2>&1 &
    sleep 2
    if pgrep -f "background_monitor.sh" > /dev/null; then
        log "✅ Background monitor started successfully"
    else
        log "⚠️ Failed to start background monitor"
    fi
else
    log "✅ Background monitor already running"
fi

# First, establish broker connection
log "🔗 Establishing broker connection..."
cd "$TRADING_DIR"
./auto_broker_connect.sh

BROKER_STATUS=$(cat "$TRADING_DIR/broker_status.txt" 2>/dev/null || echo "UNKNOWN")
log "📊 Broker Status: $BROKER_STATUS"

if [[ "$BROKER_STATUS" != *"CONNECTED"* ]]; then
    log "⚠️ Broker connection issue detected but proceeding with startup..."
    log "ℹ️ Trading system will attempt to reconnect automatically"
fi

# Start in background with nohup
nohup python3 main_papertrader.py > logs/trading_auto_$(date +%Y%m%d).log 2>&1 &
TRADING_PID=$!

# Wait and verify
sleep 5
if pgrep -f "python.*main_papertrader" > /dev/null; then
    log "✅ Trading System started successfully (PID: $TRADING_PID)"
    
    # Start dashboard if not running
    if ! pgrep -f "streamlit.*dashboard" > /dev/null; then
        log "🌐 Starting Dashboard..."
        nohup streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 > logs/dashboard_auto_$(date +%Y%m%d).log 2>&1 &
        log "✅ Dashboard started"
    fi
    
    # Create status file
    echo "RUNNING" > "$TRADING_DIR/system_status.txt"
    echo "Started: $(date)" >> "$TRADING_DIR/system_status.txt"
    
else
    log "❌ Failed to start Trading System"
    echo "FAILED" > "$TRADING_DIR/system_status.txt"
    exit 1
fi
