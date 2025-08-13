#!/bin/bash
# Auto Startup Script for Paper Trading System
# This script automatically starts the trading system at market open time

# Configuration
TRADING_DIR="/home/ubuntu/PaperTradingV1.3"
LOG_FILE="$TRADING_DIR/logs/auto_startup.log"
MARKET_START_TIME="09:00"
MARKET_END_TIME="15:30"

# Ensure logs directory exists
mkdir -p "$TRADING_DIR/logs"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if market is open
is_market_time() {
    current_time=$(date '+%H:%M')
    current_day=$(date '+%u')  # 1=Monday, 7=Sunday
    
    # Check if it's a weekday (Monday to Friday)
    if [ "$current_day" -ge 1 ] && [ "$current_day" -le 5 ]; then
        # Check if current time is between market hours
        if [[ "$current_time" > "$MARKET_START_TIME" ]] && [[ "$current_time" < "$MARKET_END_TIME" ]]; then
            return 0  # Market is open
        fi
    fi
    return 1  # Market is closed
}

# Function to check if trading system is already running
is_trading_running() {
    # Check for both possible patterns
    if pgrep -f "main_papertrader.py" > /dev/null || pgrep -f "python.*main_papertrader" > /dev/null; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

# Function to start trading system
start_trading_system() {
    log_message "🚀 Starting Paper Trading System..."
    
    cd "$TRADING_DIR"
    
    # Start main trading system in background
    nohup python3 main_papertrader.py > logs/papertrader_auto.log 2>&1 &
    TRADING_PID=$!
    
    # Wait a moment to check if it started successfully
    sleep 5
    
    if is_trading_running; then
        log_message "✅ Trading System started successfully (PID: $TRADING_PID)"
        
        # Also start dashboard if not running
        if ! pgrep -f "streamlit.*dashboard.py" > /dev/null; then
            log_message "🌐 Starting Dashboard..."
            nohup streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 > logs/dashboard_auto.log 2>&1 &
            DASHBOARD_PID=$!
            log_message "✅ Dashboard started (PID: $DASHBOARD_PID)"
        else
            log_message "ℹ️ Dashboard already running"
        fi
        
        return 0
    else
        log_message "❌ Failed to start Trading System"
        return 1
    fi
}

# Function to stop trading system
stop_trading_system() {
    log_message "🛑 Stopping Paper Trading System..."
    
    # Stop main trading system
    pkill -f "main_papertrader.py"
    
    # Wait for graceful shutdown
    sleep 10
    
    # Force kill if still running
    pkill -9 -f "main_papertrader.py" 2>/dev/null
    
    log_message "✅ Trading System stopped"
}

# Main logic
log_message "🔍 Auto Startup Check - Current time: $(date '+%H:%M'), Day: $(date '+%A')"

if is_market_time; then
    log_message "📈 Market is OPEN - Checking trading system status..."
    
    if is_trading_running; then
        log_message "ℹ️ Trading System already running - No action needed"
    else
        log_message "⚠️ Market is open but Trading System not running - Starting now..."
        start_trading_system
    fi
else
    log_message "🕒 Market is CLOSED - Checking if system should be stopped..."
    
    if is_trading_running; then
        current_time=$(date '+%H:%M')
        if [[ "$current_time" > "$MARKET_END_TIME" ]]; then
            log_message "🌙 Post-market hours - Stopping trading system..."
            stop_trading_system
        else
            log_message "🌅 Pre-market hours - Keeping system ready..."
        fi
    else
        log_message "ℹ️ Market closed and system not running - Normal state"
    fi
fi

log_message "✅ Auto Startup Check Complete"
