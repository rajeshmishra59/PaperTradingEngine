# 🚀 PAPER TRADING ENGINE - PROJECT STRUCTURE

## 📁 Root Directory Files

### 🎯 **CORE TRADING ENGINE**
- `main_papertrader.py` - Main trading bot with smart batching
- `broker_interface.py` - Angel One broker interface
- `portfolio_manager.py` - Portfolio and position management
- `database_manager.py` - SQLite database operations
- `trade_logger.py` - Trade logging and analytics
- `charge_calculator.py` - Brokerage charge calculations
- `timezone_config.py` - IST timezone management
- `config_loader.py` - Configuration management

### 📊 **DASHBOARD & VISUALIZATION**
- `dashboard.py` - **MAIN DASHBOARD** (symlink to professional version)

### 📋 **CONFIGURATION**
- `config.yml` - Main configuration file
- `requirements.txt` - Python dependencies
- `.env` - Environment variables
- `.gitignore` - Git ignore rules

### 📈 **DATA FILES**
- `trading_data.db` - SQLite trading database
- `angel_instruments.csv` - Angel One instruments
- `instruments.csv` - Processed instruments

---

## 📁 **ORGANIZED DIRECTORIES**

### 🎨 `/dashboards/` - All Dashboard Versions
- `dashboard_professional.py` - **ULTIMATE ACTIVE TRADING CONTROL CENTER** ⭐
- `dashboard_collective.py` - Collective strategies view
- `dashboard_ultimate.py` - Original ultimate version
- `dashboard_focused.py` - Active strategies only
- `dashboard_enhanced.py` - Enhanced version
- `dashboard_simple_fix.py` - Simplified version
- `debug_dashboard.py` - Debug version
- `market_viz.py` - Market visualization

### ⚙️ `/scripts/` - Automation Scripts
- `start_trading_bot.sh` - Bot startup script
- `setup_trading_env.sh` - Environment setup
- `market_monitor.sh` - Market monitoring
- `show_structure.sh` - Project structure display

### 📝 `/config_files/` - Configuration & Status
- `trading_bot_env.conf` - Bot environment config
- `broker_status.txt` - Broker connection status
- `heartbeat.txt` - System heartbeat
- `system_status.txt` - System status logs
- `system_status.json` - System status JSON

### ❌ `/deprecated/` - Old/Unused Files
- `adaptive_framework.py` - Old adaptive framework
- `data_router.py` - Old data routing
- `connect_broker.py` - Old broker connection
- `select_broker.py` - Old broker selection

### 🧠 `/strategies/` - Trading Strategies
- `base_strategy.py` - Base strategy class
- `sankhyaek_strategy.py` - SankhyaEk strategy ⭐ (Active)
- `alphaone_strategy.py` - AlphaOne strategy
- `numerouno_strategy.py` - NumeroUno strategy
- `apex_strategy.py` - Apex strategy
- `rangebound_strategy.py` - Range bound strategy
- `test_strategy.py` - Test strategy

### 📊 `/logs/` - System Logs
- `papertrading.log` - Main trading logs
- `2025-08-11/app.log` - Daily logs
- `2025-08-12/app.log` - Daily logs

### 📁 **Other Organized Directories**
- `/analysis/` - Trading analysis tools
- `/archive/` - Archived files
- `/automation/` - Automation scripts
- `/backup/` - Backup files
- `/config/` - Additional configs
- `/development/` - Development files
- `/docs/` - Documentation
- `/intelligence/` - AI/ML components
- `/optimization/` - Strategy optimization
- `/tools/` - Utility tools
- `/trading_env/` - Trading environment setup

---

## 🎯 **QUICK ACCESS**

### Start Main Dashboard:
```bash
cd /home/ubuntu/PaperTradingV1.3
streamlit run dashboard.py --server.address 0.0.0.0 --server.port 8501
```

### Start Trading Bot:
```bash
cd /home/ubuntu/PaperTradingV1.3
python3 main_papertrader.py
```

### Check System Status:
```bash
cd /home/ubuntu/PaperTradingV1.3
python3 -c "
from database_manager import DatabaseManager
db = DatabaseManager()
print('Active Strategies:')
state = db.load_full_portfolio_state()
for name, data in state.items():
    print(f'  {name}: ₹{data.get(\"trading_capital\", 0):,.0f}')
"
```

---

## 🏆 **PROJECT STATUS**
- ✅ **Trading Bot**: Live with smart batching
- ✅ **Dashboard**: Ultimate Active Trading Control Center
- ✅ **Automation**: Morning/Evening automated tasks
- ✅ **Risk Management**: Drawdown monitoring, position sizing
- ✅ **Database**: SQLite with comprehensive logging
- ✅ **Git**: Version controlled with stable commits

**Last Updated**: August 13, 2025
**Version**: 1.3 (Production Ready)
**Status**: 🟢 LIVE & OPERATIONAL
