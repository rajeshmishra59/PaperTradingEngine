# File: dashboard.py
# Hamara Visual Control Room (Final Patched Version 2.0)

import streamlit as st
import pandas as pd
import json
import time
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="Trading Control Room",
    page_icon="🤖",
    layout="wide",
)

# --- File Paths ---
CONTROL_FILE = "control_signal.txt"
STATE_FILE = "portfolio_state.json"
TRADE_LOG_FILE = "logs/paper_trades.csv"
SYSTEM_LOG_FILE = "logs/papertrading.log"


# --- Helper Functions to Load Data ---
def load_portfolio_state():
    """Loads portfolio state from the JSON file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def load_trade_log():
    """Loads the trade log CSV into a DataFrame, handles empty file."""
    if os.path.exists(TRADE_LOG_FILE) and os.path.getsize(TRADE_LOG_FILE) > 0:
        try:
            return pd.read_csv(TRADE_LOG_FILE)
        except pd.errors.EmptyDataError:
            return pd.DataFrame()
    return pd.DataFrame()

def read_live_logs(lines=20):
    """Reads the last N lines from the system log file."""
    if os.path.exists(SYSTEM_LOG_FILE):
        with open(SYSTEM_LOG_FILE, 'r', encoding='utf-8') as f:
            return "".join(f.readlines()[-lines:])
    return "Log file not found."


# --- Main Dashboard Layout ---
st.title("Trading Control Room (V1.3)")

# --- Control Panel ---
col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    if st.button("▶️ START Engine", use_container_width=True):
        with open(CONTROL_FILE, "w") as f: f.write("RUN")
        st.toast("START signal sent!", icon="✅")
with col2:
    if st.button("⏹️ STOP Engine", use_container_width=True):
        with open(CONTROL_FILE, "w") as f: f.write("STOP")
        st.toast("STOP signal sent!", icon="🛑")

st.divider()

# --- Data Display Section ---
st.header("Live Monitoring")

# --- FIX: Create placeholders for all dynamic sections ---
metrics_placeholder = st.empty()
open_positions_placeholder = st.empty()
closed_trades_placeholder = st.empty()
logs_placeholder = st.empty()


# --- Live Update Loop ---
while True:
    state = load_portfolio_state()
    trade_log = load_trade_log()
    live_logs = read_live_logs()
    
    cash_data = state.get('cash', {})
    positions_data = state.get('positions', {})
    
    # --- FIX: Update P&L Metrics inside a placeholder ---
    with metrics_placeholder.container():
        if 'initial_capital' not in st.session_state and cash_data:
            st.session_state['initial_capital'] = cash_data.copy()
        
        initial_capital = sum(st.session_state.get('initial_capital', {}).values())
        current_cash = sum(cash_data.values())
        realized_pnl = current_cash - initial_capital if initial_capital > 0 else 0
        pnl_percent = (realized_pnl / initial_capital * 100) if initial_capital > 0 else 0

        pnl_cols = st.columns(3) # Using 3 columns now
        pnl_cols[0].metric(label="Initial Capital", value=f"₹{initial_capital:,.2f}")
        pnl_cols[1].metric(label="Current Cash", value=f"₹{current_cash:,.2f}")
        pnl_cols[2].metric(label="Realized P&L", value=f"₹{realized_pnl:,.2f}", delta=f"{pnl_percent:.2f}%")
    
    # Update Open Positions Table
    open_positions_list = []
    for strategy, symbols in positions_data.items():
        for symbol, pos in symbols.items():
            pos['strategy'] = strategy
            open_positions_list.append(pos)
    
    with open_positions_placeholder.container():
        st.subheader("Open Positions")
        if open_positions_list:
            open_df = pd.DataFrame(open_positions_list).reindex(columns=['strategy', 'symbol', 'action', 'quantity', 'entry_price', 'entry_time'])
            st.dataframe(open_df, use_container_width=True)
        else:
            st.info("No open positions.")
        
    # Update Closed Trades Table
    with closed_trades_placeholder.container():
        st.subheader("Trade History")
        if not trade_log.empty:
            st.dataframe(trade_log.iloc[::-1], use_container_width=True)
        else:
            st.info("No trades logged yet.")
        
    # Update Live Logs
    with logs_placeholder.container():
        st.subheader("Live System Logs")
        st.code(live_logs, language='log')
    
    time.sleep(5)