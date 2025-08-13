#!/bin/bash
# Quick optimizer status checker
echo "🔍 OPTIMIZER STATUS:"
python3 optimizer_monitor.py --quick

echo ""
echo "📋 QUICK COMMANDS:"
echo "   Check status: python3 optimizer_monitor.py --quick"
echo "   View live logs: tail -f optimizer_background.log"
echo "   Monitor 10min: python3 optimizer_monitor.py"
echo "   Kill optimizer: pkill -f retrain_optimizer"
echo ""
echo "💡 Optimizer will complete around 19:20 IST"
