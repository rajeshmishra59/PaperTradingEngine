#!/bin/bash

# Background System Monitor for Paper Trading Bot
# यह script background में continuously चलेगा और issues पर alert भेजेगा

SCRIPT_DIR="/home/ubuntu/PaperTradingV1.3"
LOG_FILE="$SCRIPT_DIR/logs/system_monitor.log"
ALERT_LOG="$SCRIPT_DIR/logs/alerts.log"
STATUS_FILE="$SCRIPT_DIR/system_status.json"

# Create logs directory if not exists
mkdir -p "$SCRIPT_DIR/logs"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Function to send alert
send_alert() {
    local severity="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Log alert
    echo "$timestamp - [$severity] $message" >> "$ALERT_LOG"
    
    # Use dedicated alert script
    ./send_alert.sh "$severity" "$message"
}

# Function to check if process is running
check_process() {
    if pgrep -f "main_papertrader.py" > /dev/null; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

# Function to check broker connection
check_broker() {
    if [[ -f "$SCRIPT_DIR/broker_status.txt" ]]; then
        local status=$(cat "$SCRIPT_DIR/broker_status.txt")
        if [[ "$status" == *"CONNECTED"* ]]; then
            return 0  # Connected
        fi
    fi
    return 1  # Not connected
}

# Function to check market hours
is_market_hours() {
    local current_day=$(date "+%u")  # 1=Monday, 7=Sunday
    local ist_time=$(TZ=Asia/Kolkata date "+%H%M")
    
    # Check if weekday (Monday-Friday)
    if [[ "$current_day" -ge 1 && "$current_day" -le 5 ]]; then
        # Check if between 9:00 AM and 3:30 PM IST
        if [[ "$ist_time" -ge 0900 && "$ist_time" -le 1530 ]]; then
            return 0  # Market hours
        fi
    fi
    return 1  # Not market hours
}

# Function to check system health
check_system_health() {
    local issues=0
    local status_json="{"
    
    # Check if it's market hours
    if is_market_hours; then
        status_json="$status_json\"market_status\":\"OPEN\","
        
        # Check if bot should be running
        if ! check_process; then
            send_alert "HIGH" "Trading bot is not running during market hours!"
            issues=$((issues + 1))
            status_json="$status_json\"bot_status\":\"NOT_RUNNING\","
            
            # Try to restart
            log_message "Attempting to restart trading bot..."
            cd "$SCRIPT_DIR"
            ./simple_auto_start.sh &
            sleep 10
            
            if check_process; then
                send_alert "INFO" "Trading bot successfully restarted"
                status_json="$status_json\"bot_status\":\"RESTARTED\","
            else
                send_alert "CRITICAL" "Failed to restart trading bot!"
                status_json="$status_json\"bot_status\":\"FAILED_RESTART\","
            fi
        else
            status_json="$status_json\"bot_status\":\"RUNNING\","
        fi
        
        # Check broker connection
        if ! check_broker; then
            send_alert "MEDIUM" "Broker connection issue detected"
            issues=$((issues + 1))
            status_json="$status_json\"broker_status\":\"DISCONNECTED\","
            
            # Try to reconnect
            log_message "Attempting to reconnect broker..."
            cd "$SCRIPT_DIR"
            ./auto_broker_connect.sh
            
            if check_broker; then
                send_alert "INFO" "Broker connection restored"
                status_json="$status_json\"broker_status\":\"RECONNECTED\","
            else
                send_alert "HIGH" "Failed to restore broker connection!"
                status_json="$status_json\"broker_status\":\"FAILED_RECONNECT\","
            fi
        else
            status_json="$status_json\"broker_status\":\"CONNECTED\","
        fi
        
    else
        status_json="$status_json\"market_status\":\"CLOSED\","
        status_json="$status_json\"bot_status\":\"STANDBY\","
        status_json="$status_json\"broker_status\":\"STANDBY\","
    fi
    
    # Check disk space
    local disk_usage=$(df "$SCRIPT_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ "$disk_usage" -gt 90 ]]; then
        send_alert "MEDIUM" "Disk space is running low: ${disk_usage}% used"
        issues=$((issues + 1))
    fi
    status_json="$status_json\"disk_usage\":\"${disk_usage}%\","
    
    # Check log file size
    if [[ -f "$SCRIPT_DIR/logs/papertrading.log" ]]; then
        local log_size=$(du -m "$SCRIPT_DIR/logs/papertrading.log" | cut -f1)
        if [[ "$log_size" -gt 100 ]]; then
            send_alert "LOW" "Log file is getting large: ${log_size}MB"
        fi
        status_json="$status_json\"log_size\":\"${log_size}MB\","
    fi
    
    # Check memory usage
    local memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2 }')
    if [[ "$memory_usage" -gt 85 ]]; then
        send_alert "MEDIUM" "High memory usage: ${memory_usage}%"
        issues=$((issues + 1))
    fi
    status_json="$status_json\"memory_usage\":\"${memory_usage}%\","
    
    # Complete status JSON
    status_json="$status_json\"last_check\":\"$(date '+%Y-%m-%d %H:%M:%S')\","
    status_json="$status_json\"issues_count\":$issues}"
    
    # Save status to file
    echo "$status_json" > "$STATUS_FILE"
    
    return $issues
}

# Main monitoring loop
main_monitor() {
    log_message "🔍 System monitor started - PID: $$"
    send_alert "INFO" "Background system monitor activated"
    
    local check_interval=60  # Check every 60 seconds
    local last_alert_time=0
    local consecutive_failures=0
    
    while true; do
        check_system_health
        local issues=$?
        
        if [[ $issues -eq 0 ]]; then
            consecutive_failures=0
            # Log success every 10 minutes during market hours
            if is_market_hours; then
                local current_time=$(date +%s)
                if [[ $((current_time - last_alert_time)) -gt 600 ]]; then
                    log_message "✅ All systems operational"
                    last_alert_time=$current_time
                fi
            fi
        else
            consecutive_failures=$((consecutive_failures + 1))
            log_message "⚠️ Found $issues issues (consecutive failures: $consecutive_failures)"
            
            # Send escalation alert after 3 consecutive failures
            if [[ $consecutive_failures -ge 3 ]]; then
                send_alert "CRITICAL" "System has $consecutive_failures consecutive failures - manual intervention may be required"
                consecutive_failures=0  # Reset to avoid spam
            fi
        fi
        
        sleep $check_interval
    done
}

# Handle graceful shutdown
cleanup() {
    log_message "🛑 System monitor shutting down..."
    send_alert "INFO" "Background system monitor stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Check if already running
if pgrep -f "background_monitor.sh" | grep -v $$ > /dev/null; then
    echo "Background monitor is already running!"
    exit 1
fi

# Start main monitoring loop
main_monitor
