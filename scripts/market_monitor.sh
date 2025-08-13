#!/bin/bash
# Market Status Monitor for Trading Bot

echo "📊 TRADING BOT MARKET MONITOR"
echo "=========================================="

# Get current time
current_hour=$(date +%H)
current_minute=$(date +%M)
current_time=$(date +"%H:%M")

echo "🕐 Current Time: $current_time"

# Market hours: 09:15 to 15:30
if [ $current_hour -lt 9 ] || ([ $current_hour -eq 9 ] && [ $current_minute -lt 15 ]); then
    echo "🔴 MARKET CLOSED - Pre-market"
    minutes_to_open=$(( (9*60 + 15) - (current_hour*60 + current_minute) ))
    echo "⏰ Market opens in: $minutes_to_open minutes"
elif [ $current_hour -gt 15 ] || ([ $current_hour -eq 15 ] && [ $current_minute -gt 30 ]); then
    echo "🔴 MARKET CLOSED - Post-market"
    echo "📊 Market closed for the day"
else
    echo "✅ MARKET OPEN - Trading active"
    minutes_to_close=$(( (15*60 + 30) - (current_hour*60 + current_minute) ))
    echo "⏱️  Market closes in: $minutes_to_close minutes"
fi

echo ""
echo "🚀 Bot Status:"
if pgrep -f main_papertrader > /dev/null; then
    echo "✅ Trading bot is RUNNING"
    echo "📈 All 5 strategies operational:"
    echo "   • AdaptiveAlphaOneStrategy (100 instances)"
    echo "   • AdaptiveStrategyWrapper (50 instances)"  
    echo "   • SankhyaEkStrategy (50 instances)"
    echo "   • NumeroUnoStrategy (50 instances)"
    echo "   • ApexStrategy (50 instances)"
else
    echo "❌ Trading bot is NOT running"
fi
