#!/bin/bash
# HYBRID AUTOMATION SETUP
# Sets up cron jobs for evening optimization + morning validation

echo "🚀 Setting up Hybrid Optimization Automation"
echo "=============================================="

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create log directories
mkdir -p logs/evening_optimization
mkdir -p logs/morning_validation

# Create evening optimization script
cat > evening_optimization.sh << 'EOF'
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
EOF

# Create morning validation script
cat > morning_validation.sh << 'EOF'
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
EOF

# Make scripts executable
chmod +x evening_optimization.sh
chmod +x morning_validation.sh

# Test hybrid system
echo "🧪 Testing Hybrid System..."
echo "Testing evening optimization..."
python3 hybrid_optimization_system.py --mode evening

if [ $? -eq 0 ]; then
    echo "✅ Evening optimization test passed"
    
    echo "Testing morning validation..."
    python3 hybrid_optimization_system.py --mode morning
    
    if [ $? -eq 0 ]; then
        echo "✅ Morning validation test passed"
        echo "🎉 Hybrid system tests completed successfully!"
    else
        echo "❌ Morning validation test failed"
        exit 1
    fi
else
    echo "❌ Evening optimization test failed"
    exit 1
fi

# Setup cron jobs
echo "⏰ Setting up cron jobs..."

# Remove existing automation cron jobs
crontab -l | grep -v "daily_trading_automation\|evening_optimization\|morning_validation" | crontab -

# Add new hybrid cron jobs
(crontab -l 2>/dev/null; echo "# Evening Full Optimization (4:00 PM IST = 10:30 UTC)") | crontab -
(crontab -l 2>/dev/null; echo "30 10 * * 1-5 cd $SCRIPT_DIR && ./evening_optimization.sh") | crontab -
(crontab -l 2>/dev/null; echo "# Morning Quick Validation + Trading (9:00 AM IST = 3:30 UTC)") | crontab -
(crontab -l 2>/dev/null; echo "30 3 * * 1-5 cd $SCRIPT_DIR && ./morning_validation.sh") | crontab -

echo "✅ Cron jobs installed:"
echo "   • Evening: 4:00 PM IST (10:30 UTC) - Full optimization"
echo "   • Morning: 9:00 AM IST (3:30 UTC) - Quick validation + trading"

# Show current cron jobs
echo ""
echo "📅 Current cron schedule:"
crontab -l | grep -E "(evening_optimization|morning_validation)"

echo ""
echo "🎯 HYBRID AUTOMATION SETUP COMPLETE!"
echo "=================================="
echo "📁 Files created:"
echo "   • hybrid_optimization_system.py"
echo "   • evening_optimization.sh"
echo "   • morning_validation.sh"
echo ""
echo "⏰ Schedule:"
echo "   4:00 PM IST: Full optimization (all strategies, all symbols)"
echo "   9:00 AM IST: Quick validation + paper trading start"
echo ""
echo "📊 Expected timing:"
echo "   Evening: 2+ hours (unlimited time)"
echo "   Morning: ~40 seconds average"
echo ""
echo "🚀 Benefits:"
echo "   ✅ Complete daily optimization"
echo "   ✅ Fresh parameters every day"
echo "   ✅ Lightning fast morning execution"
echo "   ✅ Perfect market timing"
echo ""
echo "📝 Next steps:"
echo "   1. Monitor logs in logs/evening_optimization/ and logs/morning_validation/"
echo "   2. Check optimization results in optimized_parameters.json"
echo "   3. Review validation decisions in morning_validation.json"
echo ""
echo "🎉 READY FOR OPTIMAL TRADING AUTOMATION!"
