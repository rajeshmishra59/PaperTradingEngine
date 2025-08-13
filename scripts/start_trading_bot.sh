#!/bin/bash
# start_trading_bot.sh - Start trading bot with proper timezone configuration

# Set timezone environment variables
export TZ=Asia/Kolkata
export MARKET_TIMEZONE=Asia/Kolkata

# Navigate to bot directory
cd /home/ubuntu/PaperTradingV1.3

# Activate virtual environment
source trading_env/bin/activate

# Load environment variables
if [ -f .env_timezone ]; then
    export $(cat .env_timezone | grep -v '^#' | xargs)
fi

# Kill any existing instances
pkill -f main_papertrader || true
sleep 2

# Start the bot
echo "🚀 Starting Trading Bot with IST timezone configuration..."
nohup python3 main_papertrader.py > /dev/null 2>&1 &

# Get the PID
sleep 3
PID=$(pgrep -f main_papertrader)
if [ ! -z "$PID" ]; then
    echo "✅ Trading Bot started successfully (PID: $PID)"
    python3 -c "
import sys
sys.path.append('.')
from timezone_config import get_market_status
status = get_market_status()
print(f'📊 Market Status: {\"🟢 OPEN\" if status[\"is_market_open\"] else \"🔴 CLOSED\"}')
print(f'🕐 Current IST: {status[\"current_time_ist\"].strftime(\"%Y-%m-%d %H:%M:%S %Z\")}')
"
else
    echo "❌ Failed to start Trading Bot"
    exit 1
fi
