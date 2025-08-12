#!/bin/bash
# Evening Full Optimization (4:00 PM IST = 10:30 UTC)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="logs/evening_optimization/$(date +%Y-%m-%d).log"

echo "🌙 Starting Evening Optimization - $(date)" >> "$LOG_FILE"

# Run evening optimization
python3 hybrid_optimization_system.py --mode evening >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Evening optimization completed successfully - $(date)" >> "$LOG_FILE"
else
    echo "❌ Evening optimization failed - $(date)" >> "$LOG_FILE"
fi

echo "📊 Evening optimization finished - $(date)" >> "$LOG_FILE"
