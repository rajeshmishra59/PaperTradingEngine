#!/bin/bash

# Simple Alert Notification Script
# Usage: ./send_alert.sh "SEVERITY" "MESSAGE"

SEVERITY="$1"
MESSAGE="$2"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Load alert configuration
if [[ -f "alert_config.env" ]]; then
    source alert_config.env
fi

# Function to send desktop notification (if running GUI)
send_desktop_notification() {
    if command -v notify-send >/dev/null 2>&1; then
        case "$SEVERITY" in
            "CRITICAL"|"HIGH")
                notify-send -u critical "🚨 Trading Bot Alert" "$MESSAGE"
                ;;
            "MEDIUM")
                notify-send -u normal "⚠️ Trading Bot Warning" "$MESSAGE"
                ;;
            *)
                notify-send -u low "ℹ️ Trading Bot Info" "$MESSAGE"
                ;;
        esac
    fi
}

# Function to play sound alert
play_sound_alert() {
    if [[ "$SOUND_ALERTS" == "true" && "$SEVERITY" == "CRITICAL" ]]; then
        if command -v paplay >/dev/null 2>&1; then
            paplay /usr/share/sounds/alsa/Front_Left.wav 2>/dev/null &
        elif command -v beep >/dev/null 2>&1; then
            beep -f 1000 -l 500 2>/dev/null &
        fi
    fi
}

# Function to send webhook (example for generic webhook)
send_webhook() {
    if [[ "$WEBHOOK_ENABLED" == "true" && -n "$WEBHOOK_URL" ]]; then
        local payload="{\"text\":\"[$SEVERITY] $MESSAGE\", \"timestamp\":\"$TIMESTAMP\"}"
        curl -X POST -H "Content-Type: application/json" -d "$payload" "$WEBHOOK_URL" 2>/dev/null &
    fi
}

# Function to write to alert log
log_alert() {
    echo "[$TIMESTAMP] [$SEVERITY] $MESSAGE" >> "logs/alerts.log"
}

# Main execution
if [[ -z "$SEVERITY" || -z "$MESSAGE" ]]; then
    echo "Usage: $0 SEVERITY MESSAGE"
    echo "Example: $0 HIGH 'Trading bot stopped during market hours'"
    exit 1
fi

# Log the alert
log_alert

# Send notifications based on severity
case "$SEVERITY" in
    "CRITICAL"|"HIGH")
        echo "🚨 [$SEVERITY] $MESSAGE"
        send_desktop_notification
        play_sound_alert
        send_webhook
        ;;
    "MEDIUM")
        echo "⚠️ [$SEVERITY] $MESSAGE"
        send_desktop_notification
        send_webhook
        ;;
    "LOW"|"INFO")
        echo "ℹ️ [$SEVERITY] $MESSAGE"
        ;;
    *)
        echo "📝 [$SEVERITY] $MESSAGE"
        ;;
esac

# Rate limiting check (prevent spam)
ALERT_COUNT_FILE="/tmp/trading_bot_alert_count"
CURRENT_HOUR=$(date +%H)

if [[ -f "$ALERT_COUNT_FILE" ]]; then
    LAST_HOUR=$(cat "$ALERT_COUNT_FILE" | head -1)
    ALERT_COUNT=$(cat "$ALERT_COUNT_FILE" | tail -1)
    
    if [[ "$CURRENT_HOUR" == "$LAST_HOUR" ]]; then
        if [[ "$ALERT_COUNT" -gt "${MAX_ALERTS_PER_HOUR:-10}" ]]; then
            echo "Rate limit reached - suppressing alert"
            exit 0
        else
            echo -e "$CURRENT_HOUR\n$((ALERT_COUNT + 1))" > "$ALERT_COUNT_FILE"
        fi
    else
        echo -e "$CURRENT_HOUR\n1" > "$ALERT_COUNT_FILE"
    fi
else
    echo -e "$CURRENT_HOUR\n1" > "$ALERT_COUNT_FILE"
fi
