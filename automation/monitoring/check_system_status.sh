#!/bin/bash

# System Status Checker for Autonomous Paper Trading Bot
echo "🔍 Paper Trading Bot - System Status Check"
echo "==========================================="

# Check current time and market status
CURRENT_TIME=$(date "+%H:%M")
CURRENT_DAY=$(date "+%u")  # 1=Monday, 7=Sunday
IST_TIME=$(TZ=Asia/Kolkata date "+%H:%M")

echo "📅 Current Time (IST): $IST_TIME"
echo "📅 Day of Week: $CURRENT_DAY (1=Mon, 7=Sun)"

# Market status
if [[ "$CURRENT_DAY" -ge 1 && "$CURRENT_DAY" -le 5 ]]; then
    if [[ "$IST_TIME" > "09:00" && "$IST_TIME" < "15:30" ]]; then
        echo "📈 Market Status: OPEN ✅"
        MARKET_OPEN=true
    else
        echo "📈 Market Status: CLOSED ❌"
        MARKET_OPEN=false
    fi
else
    echo "📈 Market Status: WEEKEND ❌"
    MARKET_OPEN=false
fi

echo ""

# Check broker connection
echo "🔗 Broker Connection Status:"
if [[ -f "broker_status.txt" ]]; then
    BROKER_STATUS=$(cat broker_status.txt)
    echo "   Status: $BROKER_STATUS"
    if [[ "$BROKER_STATUS" == *"CONNECTED"* ]]; then
        echo "   Broker: ✅ Connected"
        BROKER_OK=true
    else
        echo "   Broker: ❌ Not Connected"
        BROKER_OK=false
    fi
else
    echo "   Status: No status file found"
    echo "   Broker: ❌ Unknown"
    BROKER_OK=false
fi

echo ""

# Check if trading bot is running
echo "🤖 Trading Bot Process:"
if pgrep -f "main_papertrader.py" > /dev/null; then
    PID=$(pgrep -f "main_papertrader.py")
    echo "   Process: ✅ Running (PID: $PID)"
    BOT_RUNNING=true
else
    echo "   Process: ❌ Not Running"
    BOT_RUNNING=false
fi

echo ""

# Check cron jobs
echo "⏰ Cron Jobs Status:"
CRON_COUNT=$(crontab -l 2>/dev/null | grep -c "paper")
if [[ "$CRON_COUNT" -gt 0 ]]; then
    echo "   Cron Jobs: ✅ $CRON_COUNT jobs configured"
    echo "   Active Jobs:"
    crontab -l 2>/dev/null | grep "paper" | while read line; do
        echo "      $line"
    done
else
    echo "   Cron Jobs: ❌ No automated jobs found"
fi

echo ""

# Check log files
echo "📝 Log Files:"
if [[ -f "logs/papertrading.log" ]]; then
    LOG_SIZE=$(du -h logs/papertrading.log | cut -f1)
    LAST_LOG_LINE=$(tail -1 logs/papertrading.log)
    echo "   Main Log: ✅ $LOG_SIZE"
    echo "   Last Entry: $(echo $LAST_LOG_LINE | cut -c1-80)..."
else
    echo "   Main Log: ❌ Not found"
fi

echo ""

# Overall system status
echo "🎯 Overall System Status:"
if [[ "$MARKET_OPEN" == true && "$BROKER_OK" == true && "$BOT_RUNNING" == true ]]; then
    echo "   Status: ✅ FULLY OPERATIONAL"
    echo "   🚀 All systems green - trading active!"
elif [[ "$MARKET_OPEN" == false ]]; then
    echo "   Status: 🟡 STANDBY (Market Closed)"
    echo "   💤 Waiting for market hours..."
elif [[ "$BOT_RUNNING" == false ]]; then
    echo "   Status: ❌ BOT NOT RUNNING"
    echo "   🔧 Bot needs to be started"
elif [[ "$BROKER_OK" == false ]]; then
    echo "   Status: ⚠️ BROKER ISSUE"
    echo "   🔗 Broker connection needs attention"
else
    echo "   Status: 🟡 PARTIAL OPERATION"
    echo "   🔍 Some components may need attention"
fi

echo ""
echo "💡 Quick Commands:"
echo "   Start Bot: ./simple_auto_start.sh"
echo "   Check Broker: ./auto_broker_connect.sh"
echo "   View Logs: tail -f logs/papertrading.log"
echo "   Stop Bot: pkill -f main_papertrader.py"
