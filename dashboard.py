# File: dashboard.py (Database Integrated Version)

import streamlit as st
import pandas as pd
import json
import time
import os
import re
from datetime import datetime
from database_manager import DatabaseManager

# --- 1. SETUP ---
st.set_page_config(page_title="Trading Control Room (DB)", page_icon="🚀", layout="wide")
db_manager = DatabaseManager() # Initialize a single DB connection for the dashboard

# --- 2. HELPER FUNCTIONS ---
def read_live_logs(lines=20):
    log_file = "logs/papertrading.log"
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f: return "".join(f.readlines()[-lines:])
    return "Log file not found."

# --- 3. MAIN DASHBOARD LAYOUT ---
st.title("🚀 Trading Control Room (DB Version)")

with st.container(border=True):
    col1, col2, col3_status = st.columns([1, 1, 3])
    with col1:
        if st.button("▶️ START Engine", use_container_width=True):
            with open("control_signal.txt", "w") as f: f.write("RUN"); st.toast("START signal sent!", icon="✅")
    with col2:
        if st.button("⏹️ STOP Engine", use_container_width=True):
            with open("control_signal.txt", "w") as f: f.write("STOP"); st.toast("STOP signal sent!", icon="🛑")
    with col3_status:
        engine_status = "OFFLINE"
        if os.path.exists("heartbeat.txt"):
            try:
                with open("heartbeat.txt", 'r') as f: last_heartbeat = datetime.fromisoformat(f.read())
                if (datetime.now() - last_heartbeat).total_seconds() < 150: engine_status = "RUNNING"
            except (IOError, ValueError): engine_status = "UNKNOWN"
        if os.path.exists("control_signal.txt"):
            with open("control_signal.txt", 'r') as f:
                if f.read().strip().upper() == "STOP": engine_status = "PAUSED"
        st.metric("Engine Status", engine_status)

metrics_placeholder = st.empty()
main_data_placeholder = st.empty()
logs_placeholder = st.empty()

while True:
    state = db_manager.load_full_portfolio_state()
    trade_log = db_manager.load_all_trades()
    live_logs = read_live_logs()
    
    initial_capital = {name: data['initial_capital'] for name, data in state.items()}
    cash_data = {name: data['trading_capital'] for name, data in state.items()}
    banked_profit = {name: data['banked_profit'] for name, data in state.items()}
    total_charges = {name: data['total_charges'] for name, data in state.items()}
    
    with metrics_placeholder.container(border=True):
        total_initial_capital, total_trading_capital, total_banked_profit, total_charges_paid = sum(initial_capital.values()), sum(cash_data.values()), sum(banked_profit.values()), sum(total_charges.values())
        net_pnl = total_banked_profit
        pnl_percent = (net_pnl / total_initial_capital * 100) if total_initial_capital > 0 else 0
        pnl_cols = st.columns(4)
        pnl_cols[0].metric(label="💰 Total Trading Capital", value=f"₹{total_trading_capital:,.2f}")
        pnl_cols[1].metric(label="🏦 Total Banked Profit (Net P&L)", value=f"₹{total_banked_profit:,.2f}", delta=f"{pnl_percent:.2f}%")
        pnl_cols[2].metric(label="🧾 Total Charges Paid", value=f"₹{total_charges_paid:,.2f}")
        pnl_cols[3].metric(label="📈 Initial Capital", value=f"₹{total_initial_capital:,.2f}")

    with main_data_placeholder.container():
        col1_data, col2_data = st.columns(2)
        with col1_data:
            with st.container(border=True):
                st.markdown("### 📊 Capital Curve")
                if not trade_log.empty and total_initial_capital > 0 and 'details' in trade_log.columns:
                    exit_trades = trade_log[trade_log['action'].str.contains('EXIT|FORCE EXIT', na=False)].copy()
                    def parse_pnl(detail_str):
                        if not isinstance(detail_str, str): return 0.0
                        match = re.search(r"PnL:\s*(-?[\d,]+\.\d{2})", detail_str)
                        return float(match.group(1).replace(",", "")) if match else 0.0
                    exit_trades['PnL'] = exit_trades['details'].apply(parse_pnl)
                    if not exit_trades.empty:
                        exit_trades['timestamp'] = pd.to_datetime(exit_trades['timestamp'])
                        exit_trades = exit_trades.sort_values(by='timestamp')
                        exit_trades['Equity'] = total_initial_capital + exit_trades['PnL'].cumsum()
                        st.line_chart(exit_trades.set_index('timestamp')['Equity'])
                    else: st.info("Waiting for the first closed trade to plot.")
                else: st.info("Waiting for the first closed trade to plot.")
            
            with st.container(border=True):
                st.markdown("### 🟢 Open Positions")
                st.info("Live position data will be re-integrated in a future version.")

        with col2_data:
            with st.container(border=True):
                st.markdown("### 🧠 Strategy Performance")
                summary_data = []
                for strat_name in initial_capital:
                    summary_data.append({"Strategy": strat_name, "Trading Capital": cash_data.get(strat_name, 0), "Banked Profit": banked_profit.get(strat_name, 0), "Charges Paid": total_charges.get(strat_name, 0)})
                if summary_data:
                    st.dataframe(pd.DataFrame(summary_data).set_index("Strategy").style.format("₹{:,.2f}"), use_container_width=True)
                else: st.info("Waiting for engine to initialize...")
            
            with st.container(border=True):
                st.markdown("### 📜 Trade History")
                if not trade_log.empty:
                    display_log = trade_log.rename(columns={'strategy_name': 'Strategy', 'symbol': 'Symbol', 'action': 'Action', 'price': 'Price', 'quantity': 'Quantity', 'details': 'Details', 'timestamp': 'Timestamp'})
                    st.dataframe(display_log.iloc[::-1], use_container_width=True)
                else:
                    st.info("No trades logged yet.")
    
    with logs_placeholder.container(border=True):
        st.markdown("### 💻 Live System Logs"); st.code(live_logs, language='log')
    
    time.sleep(5)