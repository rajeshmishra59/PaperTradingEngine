#!/bin/bash
# Quick project structure viewer

echo "🎯 PAPERTRADING V1.3 - CLEAN STRUCTURE"
echo "======================================"

echo ""
echo "📊 CORE FILES (Root):"
ls -1 *.py *.csv *.db *.txt *.md 2>/dev/null | head -15

echo ""
echo "📁 ORGANIZED FOLDERS:"
echo "   📊 analysis/     - Trading analysis & reports"
echo "   🤖 automation/   - Automation scripts & configs"  
echo "   ⚡ optimization/ - Background optimization"
echo "   🧠 intelligence/ - AI & pre-market analysis"
echo "   🛠️ tools/        - Utilities & debugging"
echo "   📚 docs/         - Documentation & guides"
echo "   🗂️ logs/         - System logs by category"
echo "   📦 strategies/   - Trading strategies"

echo ""
echo "🚀 BACKGROUND PROCESSES:"
ps aux | grep -E "(retrain_optimizer|python.*automation)" | grep -v grep | head -3

echo ""
echo "💡 QUICK ACCESS:"
echo "   Status:    ./optimization/background/check_optimizer.sh"
echo "   Monitor:   python3 analysis/monitoring/daily_monitor.py"
echo "   Analysis:  python3 analysis/pnl/smart_trade_analyzer.py"
echo "   Structure: ./show_structure.sh"
