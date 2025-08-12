#!/bin/bash
# Cron Job Setup Script for Daily Trading Automation
# This script sets up automated daily trading at 9:00 AM

echo "🚀 Setting up Daily Trading Automation..."

# Get the current user
USER=$(whoami)
TRADING_DIR="/home/ubuntu/PaperTradingV1.3"

echo "📁 Trading Directory: $TRADING_DIR"
echo "👤 User: $USER"

# Make the automation script executable
chmod +x "$TRADING_DIR/daily_trading_automation.py"

# Create cron job entry for IST timezone (3:30 AM UTC = 9:00 AM IST)
CRON_ENTRY="30 3 * * 1-5 cd $TRADING_DIR && /usr/bin/python3 $TRADING_DIR/daily_trading_automation.py >> $TRADING_DIR/logs/cron.log 2>&1"

echo "📝 Cron job entry:"
echo "$CRON_ENTRY"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "daily_trading_automation.py"; then
    echo "⚠️ Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "daily_trading_automation.py" | crontab -
fi

# Add new cron job
echo "➕ Adding new cron job..."
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

# Verify cron job was added
echo "✅ Current cron jobs:"
crontab -l

echo ""
echo "🎉 Daily Trading Automation Setup Complete!"
echo ""
echo "📋 Summary:"
echo "  • Automation runs Monday-Friday at 9:00 AM IST (3:30 AM UTC)"
echo "  • First runs retrain_optimizer.py"
echo "  • Then runs main_papertrader.py"
echo "  • Logs saved to: $TRADING_DIR/logs/"
echo ""
echo "🔧 Management Commands:"
echo "  • View cron jobs: crontab -l"
echo "  • Remove cron job: crontab -e (then delete the line)"
echo "  • View automation logs: tail -f $TRADING_DIR/logs/automation_$(date +%Y-%m-%d).log"
echo "  • View cron logs: tail -f $TRADING_DIR/logs/cron.log"
echo ""
echo "🧪 To test automation manually:"
echo "  cd $TRADING_DIR && python3 daily_trading_automation.py"
