#!/bin/bash
# Trading Automation Management Script
# Provides easy commands to manage daily trading automation

TRADING_DIR="/home/ubuntu/PaperTradingV1.3"
AUTOMATION_SCRIPT="daily_trading_automation.py"

show_help() {
    echo "🚀 Trading Automation Manager"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup     - Set up daily automation (9 AM Monday-Friday)"
    echo "  remove    - Remove automation cron job"
    echo "  status    - Show automation status"
    echo "  test      - Run automation manually (for testing)"
    echo "  logs      - Show today's automation logs"
    echo "  cron-logs - Show cron execution logs"
    echo "  help      - Show this help message"
    echo ""
}

setup_automation() {
    echo "🔧 Setting up daily trading automation..."
    bash "$TRADING_DIR/setup_automation.sh"
}

remove_automation() {
    echo "🗑️ Removing trading automation..."
    if crontab -l 2>/dev/null | grep -q "daily_trading_automation.py"; then
        crontab -l 2>/dev/null | grep -v "daily_trading_automation.py" | crontab -
        echo "✅ Automation cron job removed"
    else
        echo "ℹ️ No automation cron job found"
    fi
}

show_status() {
    echo "📊 Trading Automation Status"
    echo "================================"
    
    # Check if cron job exists
    if crontab -l 2>/dev/null | grep -q "daily_trading_automation.py"; then
        echo "✅ Cron job: ACTIVE"
        echo "📅 Schedule: Daily at 9:00 AM (Monday-Friday)"
        echo ""
        echo "Current cron job:"
        crontab -l 2>/dev/null | grep "daily_trading_automation.py"
    else
        echo "❌ Cron job: NOT CONFIGURED"
        echo "Run '$0 setup' to configure automation"
    fi
    
    echo ""
    echo "📁 Files:"
    echo "  Automation script: $(ls -la "$TRADING_DIR/$AUTOMATION_SCRIPT" 2>/dev/null || echo 'NOT FOUND')"
    echo "  Setup script: $(ls -la "$TRADING_DIR/setup_automation.sh" 2>/dev/null || echo 'NOT FOUND')"
    
    echo ""
    echo "📋 Recent logs:"
    if ls "$TRADING_DIR/logs/automation_"*.log 1> /dev/null 2>&1; then
        echo "  Latest automation log: $(ls -t "$TRADING_DIR/logs/automation_"*.log | head -1)"
    else
        echo "  No automation logs found"
    fi
    
    if [ -f "$TRADING_DIR/logs/cron.log" ]; then
        echo "  Cron log: $TRADING_DIR/logs/cron.log"
    else
        echo "  No cron log found"
    fi
}

test_automation() {
    echo "🧪 Running automation manually for testing..."
    cd "$TRADING_DIR"
    python3 "$AUTOMATION_SCRIPT"
}

show_automation_logs() {
    TODAY=$(date +%Y-%m-%d)
    LOG_FILE="$TRADING_DIR/logs/automation_$TODAY.log"
    
    if [ -f "$LOG_FILE" ]; then
        echo "📄 Today's automation log ($TODAY):"
        echo "================================"
        tail -50 "$LOG_FILE"
    else
        echo "ℹ️ No automation log found for today ($TODAY)"
        echo ""
        echo "Available automation logs:"
        ls -la "$TRADING_DIR/logs/automation_"*.log 2>/dev/null || echo "None found"
    fi
}

show_cron_logs() {
    CRON_LOG="$TRADING_DIR/logs/cron.log"
    
    if [ -f "$CRON_LOG" ]; then
        echo "📄 Cron execution log:"
        echo "======================"
        tail -50 "$CRON_LOG"
    else
        echo "ℹ️ No cron log found at $CRON_LOG"
    fi
}

# Main script logic
case "$1" in
    "setup")
        setup_automation
        ;;
    "remove")
        remove_automation
        ;;
    "status")
        show_status
        ;;
    "test")
        test_automation
        ;;
    "logs")
        show_automation_logs
        ;;
    "cron-logs")
        show_cron_logs
        ;;
    "help"|"--help"|"-h"|"")
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
