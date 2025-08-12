# 📊 PaperTradingV1.3 - Organized Structure

## 🎯 Core Trading Files (Root Directory)
```
├── main_papertrader.py         # Main trading engine
├── broker_interface.py         # Broker connectivity
├── connect_broker.py           # Broker connection handler
├── portfolio_manager.py        # Portfolio management
├── database_manager.py         # Database operations
├── dashboard.py               # Trading dashboard
├── trade_logger.py            # Trade logging
├── config_loader.py           # Configuration loader
├── data_router.py             # Data routing
├── charge_calculator.py       # Brokerage charges
├── select_broker.py           # Broker selection
├── zerodha_login.py           # Zerodha authentication
├── enhanced_morning_validation.py  # Morning validation
├── strategies/                # Trading strategies folder
├── trading_data.db            # SQLite database
├── instruments.csv            # Trading instruments
├── angel_instruments.csv      # Angel One instruments
└── requirements.txt           # Python dependencies
```

## 📁 Organized Folder Structure

### 📊 `/analysis/` - Trading Analysis
```
├── pnl/                      # P&L analysis tools
├── reports/                  # Trading reports
└── monitoring/              # Real-time monitoring
```

### 🤖 `/automation/` - Automation System
```
├── scripts/                 # Automation scripts
├── configs/                 # Configuration files
└── schedules/               # Cron schedules
```

### ⚡ `/optimization/` - Optimization System
```
├── background/              # Background optimization
├── params/                  # Parameter files
└── timing/                  # Timing optimization
```

### 🧠 `/intelligence/` - AI & Intelligence
```
├── premarket/              # Pre-market analysis
├── adaptive/               # Adaptive systems
└── ml/                     # Machine learning
```

### 🛠️ `/tools/` - Utilities & Tools
```
├── monitors/               # Monitoring tools
├── utilities/              # General utilities
└── debug/                  # Debugging tools
```

### 📚 `/docs/` - Documentation
```
├── guides/                 # User guides
├── summaries/              # System summaries
└── roadmaps/               # Development roadmaps
```

### 🗂️ `/logs/` - Log Files
```
├── premarket_intelligence/ # Pre-market logs
├── morning_validation/     # Morning validation logs
├── evening_optimization/   # Evening optimization logs
└── [date]/                 # Daily log folders
```

## 🚀 Quick Commands

### Daily Operations
```bash
# Check optimizer status
./optimization/background/check_optimizer.sh

# Run daily monitor
python3 analysis/monitoring/daily_monitor.py

# Manual automation setup
./automation/scripts/setup_enhanced_automation.sh
```

### Analysis & Reports
```bash
# PnL analysis
python3 analysis/pnl/smart_trade_analyzer.py

# Root cause analysis
python3 analysis/reports/root_cause_analysis.py

# Real-time monitoring
python3 analysis/monitoring/daily_monitor.py
```

### Intelligence Systems
```bash
# Pre-market analysis
python3 intelligence/premarket/premarket_intelligence.py

# Adaptive framework
python3 intelligence/adaptive/adaptive_framework.py
```

## 🎯 Current Status
- ✅ **Core trading system**: Operational
- ✅ **Background optimization**: Running (PID: 36422)
- ✅ **File organization**: Complete
- ✅ **Automation**: Ready for tomorrow
- ⏰ **Next optimization**: Scheduled for 4:00 PM daily

## 📞 Support Commands
```bash
# System status
./optimization/background/check_optimizer.sh

# View live logs
tail -f logs/morning_validation/latest.log

# Emergency stop
pkill -f retrain_optimizer
```
