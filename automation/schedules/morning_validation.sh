#!/bin/bash
# Morning Quick Validation (9:00 AM IST = 3:30 UTC)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="logs/morning_validation/$(date +%Y-%m-%d).log"

echo "🌅 Starting Morning Validation - $(date)" >> "$LOG_FILE"

# Run morning validation
python3 hybrid_optimization_system.py --mode morning >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Morning validation completed - $(date)" >> "$LOG_FILE"
    
    # Start paper trading after validation
    echo "🚀 Starting Paper Trading - $(date)" >> "$LOG_FILE"
    nohup python3 main_papertrader.py >> logs/morning_validation/papertrading_$(date +%Y-%m-%d).log 2>&1 &
    
    echo "📈 Paper trading started - $(date)" >> "$LOG_FILE"
else
    echo "❌ Morning validation failed - $(date)" >> "$LOG_FILE"
    echo "⚠️ Paper trading NOT started due to validation failure" >> "$LOG_FILE"
fi
