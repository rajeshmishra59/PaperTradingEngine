# File: dashboard.py
# Control Room V2.4 (Final UI Syntax Fix)

import streamlit as st
import pandas as pd
import json
import time
import os
import re
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(page_title="Trading Control Room v2.4", page_icon="🚀", layout="wide")

# --- File Paths ---
CONTROL_FILE, STATE_FILE, TRADE_LOG_FILE, SYSTEM_LOG_FILE, EXIT_COMMAND_FILE, HEARTBEAT_FILE = "control_signal.txt", "portfolio_state.json", "logs/paper_trades.csv", "logs/papertrading.log", "exit_command.txt", "heartbeat.txt"

# --- Helper Functions ---
def load_portfolio_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f: return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError): return {}
    return {}

def load_trade_log():
    if os.path.exists(TRADE_LOG_FILE) and os.path.getsize(TRADE_LOG_FILE) > 0:
        try:
            return pd.read_csv(TRADE_LOG_FILE)
        except pd.errors.EmptyDataError: return pd.DataFrame()
    return pd.DataFrame()

def read_live_logs(lines=20):
    if os.path.exists(SYSTEM_LOG_FILE):
        with open(SYSTEM_LOG_FILE, 'r', encoding='utf-8') as f: return "".join(f.readlines()[-lines:])
    return "Log file not found."

# --- Main Dashboard Layout ---
st.title("🚀 Trading Control Room (V2.4)")

with st.container(border=True):
    col1, col2, col3_status = st.columns([1, 1, 3])
    with col1:
        if st.button("▶️ START Engine", use_container_width=True):
            with open(CONTROL_FILE, "w") as f: f.write("RUN"); st.toast("START signal sent!", icon="✅")
    with col2:
        if st.button("⏹️ STOP Engine", use_container_width=True):
            with open(CONTROL_FILE, "w") as f: f.write("STOP"); st.toast("STOP signal sent!", icon="🛑")
    with col3_status:
        engine_status = "OFFLINE"
        if os.path.exists(HEARTBEAT_FILE):
            try:
                with open(HEARTBEAT_FILE, 'r') as f: last_heartbeat = datetime.fromisoformat(f.read())
                if (datetime.now() - last_heartbeat).total_seconds() < 150: engine_status = "RUNNING"
            except (IOError, ValueError):
                engine_status = "UNKNOWN"
        if os.path.exists(CONTROL_FILE):
            with open(CONTROL_FILE, 'r') as f:
                if f.read().strip().upper() == "STOP": engine_status = "PAUSED"
        st.metric("Engine Status", engine_status)

metrics_placeholder = st.empty()
main_data_placeholder = st.empty()
logs_placeholder = st.empty()

while True:
    state, trade_log, live_logs = load_portfolio_state(), load_trade_log(), read_live_logs()
    cash_data, positions_data, banked_profit, total_charges, initial_capital = state.get('cash',{}), state.get('positions',{}), state.get('banked_profit',{}), state.get('total_charges',{}), state.get('initial_capital',{})
    
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
                if not trade_log.empty and total_initial_capital > 0 and 'Details' in trade_log.columns:
                    exit_trades = trade_log[trade_log['Action'].str.contains('EXIT|FORCE EXIT', na=False)].copy()
                    def parse_pnl(detail_str):
                        if not isinstance(detail_str, str): return 0.0
                        match = re.search(r"PnL:\s*(-?[\d,]+\.\d{2})", detail_str)
                        return float(match.group(1).replace(",", "")) if match else 0.0
                    exit_trades['PnL'] = exit_trades['Details'].apply(parse_pnl)
                    if not exit_trades.empty:
                        exit_trades['Timestamp'] = pd.to_datetime(exit_trades['Timestamp'])
                        exit_trades = exit_trades.sort_values(by='Timestamp')
                        exit_trades['Equity'] = total_initial_capital + exit_trades['PnL'].cumsum()
                        st.line_chart(exit_trades.set_index('Timestamp')['Equity'])
                    else: st.info("Waiting for the first closed trade to plot.")
                else: st.info("Waiting for the first closed trade to plot.")
            with st.container(border=True):
                st.markdown("### 🟢 Open Positions")
                has_positions = any(positions_data.values())
                if has_positions:
                    for strategy, symbols in positions_data.items():
                        for symbol, pos in symbols.items():
                            c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 1, 1, 2, 1])
                            c1.text(f"{strategy}"); c2.text(f"{symbol}"); c3.text(f"{pos['action']}"); c4.text(f"{pos['quantity']}"); c5.text(f"₹{pos['entry_price']:.2f}")
                            if c6.button("Exit", key=f"exit_{strategy}_{symbol}", type="primary", use_container_width=True):
                                with open(EXIT_COMMAND_FILE, "w") as f: f.write(f"{strategy},{symbol}"); st.toast(f"Force Exit sent for {symbol}!", icon="⚠️")
                else: st.info("No open positions.")
        with col2_data:
            with st.container(border=True):
                st.markdown("### 🧠 Strategy Performance")
                summary_data = []
                for strat_name in state.get('initial_capital', {}):
                    summary_data.append({"Strategy": strat_name, "Trading Capital": cash_data.get(strat_name, 0), "Banked Profit": banked_profit.get(strat_name, 0), "Charges Paid": total_charges.get(strat_name, 0)})
                if summary_data:
                    st.dataframe(pd.DataFrame(summary_data).set_index("Strategy").style.format("₹{:,.2f}"), use_container_width=True)
                else: st.info("Waiting for engine to initialize...")
            with st.container(border=True):
                st.markdown("### 📜 Trade History")
                # --- FIX: Changed the one-liner if/else to a proper block ---
                if not trade_log.empty:
                    st.dataframe(trade_log.iloc[::-1], use_container_width=True)
                else:
                    st.info("No trades logged yet.")
    
    with logs_placeholder.container(border=True):
        st.markdown("### 💻 Live System Logs")
        st.code(live_logs, language='log')
    
    time.sleep(5)