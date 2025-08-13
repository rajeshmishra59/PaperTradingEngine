#!/bin/bash
# setup_trading_env.sh - Set up permanent timezone configuration for trading bot

echo "🚀 Setting up Trading Bot Environment with Permanent Timezone Configuration"
echo "============================================================================"

# Create virtual environment if it doesn't exist
if [ ! -d "trading_env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv trading_env
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source trading_env/bin/activate

# Install required packages
echo "📋 Installing/updating required packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Set permanent timezone environment variables
echo "🌍 Setting up permanent timezone configuration..."

# Create environment file for the bot
cat > .env_timezone << EOF
# Permanent timezone configuration for trading bot
TZ=Asia/Kolkata
PYTHONPATH=.
# Trading bot specific settings
MARKET_TIMEZONE=Asia/Kolkata
LOG_TIMEZONE=Asia/Kolkata
EOF

# Add timezone setup to bashrc for this project
BASHRC_ENTRY="# Trading Bot Timezone Configuration
export TZ=Asia/Kolkata
export MARKET_TIMEZONE=Asia/Kolkata"

# Check if already added to avoid duplicates
if ! grep -q "Trading Bot Timezone Configuration" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "$BASHRC_ENTRY" >> ~/.bashrc
    echo "✅ Added timezone configuration to ~/.bashrc"
fi

# Create systemd environment file (for production deployment)
sudo mkdir -p /etc/systemd/system
cat > trading_bot_env.conf << EOF
[Unit]
Description=Trading Bot Environment Configuration

[Service]
Environment=TZ=Asia/Kolkata
Environment=MARKET_TIMEZONE=Asia/Kolkata
Environment=PYTHONPATH=/home/ubuntu/PaperTradingV1.3
EOF

echo "✅ Environment configuration files created"

# Test timezone configuration
echo "🧪 Testing timezone configuration..."
python3 -c "
import sys
sys.path.append('.')
from timezone_config import TimezoneManager
tm = TimezoneManager()
tm.log_timezone_info()
print('✅ Timezone configuration test passed!')
"

# Create startup script that ensures timezone is set
cat > start_trading_bot.sh << 'EOF'
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
EOF

chmod +x start_trading_bot.sh
chmod +x setup_trading_env.sh

echo ""
echo "🎉 SETUP COMPLETE!"
echo "=================="
echo "✅ Virtual environment created: trading_env/"
echo "✅ Timezone configuration: timezone_config.py"
echo "✅ Environment files: .env_timezone"
echo "✅ Startup script: start_trading_bot.sh"
echo ""
echo "🚀 To start the bot with permanent timezone configuration:"
echo "   ./start_trading_bot.sh"
echo ""
echo "🔧 To test timezone configuration:"
echo "   python3 timezone_config.py"
