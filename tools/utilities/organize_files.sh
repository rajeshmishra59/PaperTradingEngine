#!/bin/bash
"""
FILE ORGANIZATION SCRIPT
Clean up and organize all files into proper folders
"""

echo "🧹 ORGANIZING PROJECT FILES..."
echo "================================"

# Create organized folder structure
mkdir -p analysis/{pnl,reports,monitoring}
mkdir -p automation/{scripts,configs,schedules}
mkdir -p optimization/{background,params,timing}
mkdir -p intelligence/{premarket,adaptive,ml}
mkdir -p tools/{monitors,utilities,debug}
mkdir -p docs/{guides,summaries,roadmaps}
mkdir -p backup/old_files

echo "📁 Created folder structure..."

# Move files to appropriate folders

# Analysis files
mv *trade_analyzer* analysis/pnl/ 2>/dev/null
mv *pnl_calculator* analysis/pnl/ 2>/dev/null
mv *investigation* analysis/reports/ 2>/dev/null
mv daily_monitor.py analysis/monitoring/ 2>/dev/null
mv daily_report_* analysis/reports/ 2>/dev/null
mv daily_stats_* analysis/reports/ 2>/dev/null
mv comprehensive_trade_report.json analysis/reports/ 2>/dev/null
mv root_cause_analysis.json analysis/reports/ 2>/dev/null
mv real_pnl_analysis.json analysis/reports/ 2>/dev/null

# Automation files
mv *automation* automation/scripts/ 2>/dev/null
mv setup_*.sh automation/scripts/ 2>/dev/null
mv manage_automation.sh automation/scripts/ 2>/dev/null
mv enhanced_morning_validation.sh automation/schedules/ 2>/dev/null
mv evening_optimization.sh automation/schedules/ 2>/dev/null
mv morning_validation.sh automation/schedules/ 2>/dev/null
mv *config.yml automation/configs/ 2>/dev/null
mv enhanced_morning_validation.json automation/configs/ 2>/dev/null
mv morning_validation.json automation/configs/ 2>/dev/null

# Optimization files
mv retrain_optimizer.py optimization/background/ 2>/dev/null
mv optimizer_monitor.py optimization/background/ 2>/dev/null
mv check_optimizer.sh optimization/background/ 2>/dev/null
mv optimizer_background.log optimization/background/ 2>/dev/null
mv hybrid_optimization_system.py optimization/timing/ 2>/dev/null
mv optimal_timing_strategy.py optimization/timing/ 2>/dev/null
mv timing_*.py optimization/timing/ 2>/dev/null
mv *params*.json optimization/params/ 2>/dev/null
mv live_params.json optimization/params/ 2>/dev/null

# Intelligence files
mv premarket_intelligence.py intelligence/premarket/ 2>/dev/null
mv test_premarket_intelligence.py intelligence/premarket/ 2>/dev/null
mv sample_premarket_report.txt intelligence/premarket/ 2>/dev/null
mv adaptive_framework.py intelligence/adaptive/ 2>/dev/null
mv test_adaptive_system.py intelligence/adaptive/ 2>/dev/null
mv integrate_adaptive_system.py intelligence/adaptive/ 2>/dev/null
mv ml_regime_detector.py intelligence/ml/ 2>/dev/null
mv smart_*.py intelligence/ml/ 2>/dev/null

# Tools and utilities
mv db_inspector.py tools/debug/ 2>/dev/null
mv quick_timing_test.py tools/debug/ 2>/dev/null
mv trading_optimizer.py tools/utilities/ 2>/dev/null

# Documentation
mv *.md docs/guides/ 2>/dev/null
mv AUTOMATION_GUIDE.md docs/guides/ 2>/dev/null
mv automation_summary.md docs/summaries/ 2>/dev/null
mv implementation_roadmap.md docs/roadmaps/ 2>/dev/null

# Analysis JSON files that might have been missed
mv trading_optimization_plan.json analysis/reports/ 2>/dev/null

echo "✅ Files organized into folders!"

# Show new structure
echo ""
echo "📊 NEW PROJECT STRUCTURE:"
echo "========================="
tree -L 2 -d . 2>/dev/null || find . -type d -not -path './.git*' -not -path './__pycache__*' -not -path './.venv*' | head -20

echo ""
echo "🎯 CORE FILES REMAINING IN ROOT:"
echo "================================"
ls -la *.py *.yml *.csv *.db 2>/dev/null | head -10

echo ""
echo "✨ Organization complete!"
