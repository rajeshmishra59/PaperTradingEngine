# File: dashboard.py (Upgraded Professional Version)
# This version features interactive charts, detailed analytics, and live position tracking.

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import os
import re
from datetime import datetime
from database_manager import DatabaseManager

# --- 1. SETUP ---
st.set_page_config(page_title="Trading Control Room", page_icon="🚀", layout="wide")
# Use a session state to initialize the DB manager once, preventing re-connections on every refresh
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
db_manager = st.session_state.db_manager

# --- 2. HELPER & DATA PROCESSING FUNCTIONS ---

def read_live_logs(lines=30):
    """Reads the last N lines from the log file."""
    log_file = "logs/papertrading.log"
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            return "".join(f.readlines()[-lines:])
    return "Log file not found."

def parse_pnl(detail_str: str) -> float:
    """Extracts PnL value from the trade details string using regex."""
    if not isinstance(detail_str, str):
        return 0.0
    match = re.search(r"PnL:\s*(-?[\d,]+\.\d{2})", detail_str)
    return float(match.group(1).replace(",", "")) if match else 0.0

@st.cache_data(ttl=5) # Cache data for 5 seconds to improve performance
def get_dashboard_data():
    """Fetches all required data from the database in one go."""
    state = db_manager.load_full_portfolio_state()
    trade_log = db_manager.load_all_trades()
    open_positions_raw = db_manager.load_all_open_positions()
    return state, trade_log, open_positions_raw

def calculate_strategy_metrics(trade_log_df):
    """Calculates detailed performance metrics for each strategy."""
    if trade_log_df.empty:
        return pd.DataFrame()

    exit_trades = trade_log_df[trade_log_df['action'].str.contains('EXIT', na=False)].copy()
    if exit_trades.empty:
        return pd.DataFrame()
        
    exit_trades['PnL'] = exit_trades['details'].apply(parse_pnl)
    
    summary = exit_trades.groupby('strategy_name').agg(
        total_trades=('PnL', 'count'),
        winning_trades=('PnL', lambda pnl: (pnl > 0).sum()),
        losing_trades=('PnL', lambda pnl: (pnl <= 0).sum()),
        total_pnl=('PnL', 'sum')
    )
    summary['win_rate_pct'] = (summary['winning_trades'] / summary['total_trades'] * 100).fillna(0)
    summary['avg_pnl_per_trade'] = (summary['total_pnl'] / summary['total_trades']).fillna(0)
    return summary

def format_open_positions(open_positions_raw):
    """Formats the raw open positions data for display."""
    positions_list = []
    for strat, symbols in open_positions_raw.items():
        for symbol, details in symbols.items():
            pos = {
                "Strategy": strat,
                "Symbol": symbol,
                "Action": details.get('action'),
                "Qty": details.get('quantity'),
                "Entry Price": details.get('entry_price'),
                "Entry Time": details.get('entry_time'),
                "SL": details.get('stop_loss'),
                "Target": details.get('target')
            }
            positions_list.append(pos)
    return pd.DataFrame(positions_list)

def calculate_live_pnl(open_positions_raw):
    """
    Calculates the total unrealized P&L from all open positions.
    This now works because portfolio_manager.py saves the 'current_price'.
    """
    total_unrealized_pnl = 0
    for strat, symbols in open_positions_raw.items():
        for symbol, details in symbols.items():
            entry_price = details.get('entry_price', 0)
            quantity = details.get('quantity', 0)
            action = details.get('action', '')
            # This now reads the price updated by the engine
            current_price = details.get('current_price', entry_price)

            if action == 'LONG':
                pnl = (current_price - entry_price) * quantity
            elif action == 'SHORT':
                pnl = (entry_price - current_price) * quantity
            else:
                pnl = 0
            total_unrealized_pnl += pnl
    return total_unrealized_pnl


# --- 3. MAIN DASHBOARD LAYOUT ---
st.title("🚀 Trading Control Room")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- Controls and Status ---
with st.container(border=True):
    col1, col2, col3_status = st.columns([1, 1, 3])
    with col1:
        if st.button("▶️ START Engine", use_container_width=True, type="primary"):
            with open("control_signal.txt", "w") as f: f.write("RUN"); st.toast("START signal sent!", icon="✅")
    with col2:
        if st.button("⏹️ STOP Engine", use_container_width=True):
            with open("control_signal.txt", "w") as f: f.write("STOP"); st.toast("STOP signal sent!", icon="🛑")
    with col3_status:
        engine_status = "OFFLINE"
        status_color = "red"
        if os.path.exists("heartbeat.txt"):
            try:
                with open("heartbeat.txt", 'r') as f: last_heartbeat = datetime.fromisoformat(f.read())
                if (datetime.now() - last_heartbeat).total_seconds() < 150:
                    engine_status = "RUNNING"
                    status_color = "green"
            except (IOError, ValueError): engine_status = "UNKNOWN"
        if os.path.exists("control_signal.txt"):
            with open("control_signal.txt", 'r') as f:
                if f.read().strip().upper() == "STOP":
                    engine_status = "PAUSED"
                    status_color = "orange"
        st.markdown(f"**Engine Status:** <span style='color:{status_color};'>●</span> {engine_status}", unsafe_allow_html=True)


# --- Placeholders for live updates ---
metrics_placeholder = st.empty()
main_data_placeholder = st.empty()
logs_placeholder = st.empty()

# --- Data Fetching ---
# Fetch all data
state, trade_log, open_positions_raw = get_dashboard_data()
live_logs = read_live_logs()

# --- KPIs Section ---
initial_capital_total = sum(data['initial_capital'] for data in state.values())
trading_capital_total = sum(data['trading_capital'] for data in state.values())
banked_profit_total = sum(data['banked_profit'] for data in state.values())
charges_total = sum(data['total_charges'] for data in state.values())

live_pnl = calculate_live_pnl(open_positions_raw)

net_pnl = banked_profit_total
pnl_percent = (net_pnl / initial_capital_total * 100) if initial_capital_total > 0 else 0

with metrics_placeholder.container(border=True):
    pnl_cols = st.columns(5)
    pnl_cols[0].metric(label="💰 Total Trading Capital", value=f"₹{trading_capital_total:,.2f}")
    pnl_cols[1].metric(label="💸 Live P&L (Unrealized)", value=f"₹{live_pnl:,.2f}", delta=f"{live_pnl:,.2f}")
    pnl_cols[2].metric(label="🏦 Banked Profit (Realized P&L)", value=f"₹{net_pnl:,.2f}", delta=f"{pnl_percent:.2f}%")
    pnl_cols[3].metric(label="🧾 Total Charges Paid", value=f"₹{charges_total:,.2f}")
    pnl_cols[4].metric(label="📈 Initial Capital", value=f"₹{initial_capital_total:,.2f}")

# --- Main Data Section ---
with main_data_placeholder.container():
    col1_data, col2_data = st.columns([2, 3]) 
    
    with col1_data:
        # --- Interactive Equity Curve ---
        with st.container(border=True):
            st.markdown("### 💹 Capital Curve")
            if not trade_log.empty and initial_capital_total > 0:
                exit_trades = trade_log[trade_log['action'].str.contains('EXIT', na=False)].copy()
                if not exit_trades.empty:
                    exit_trades['PnL'] = exit_trades['details'].apply(parse_pnl)
                    exit_trades['timestamp'] = pd.to_datetime(exit_trades['timestamp'])
                    exit_trades = exit_trades.sort_values(by='timestamp')
                    exit_trades['Equity'] = initial_capital_total + exit_trades['PnL'].cumsum()
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=exit_trades['timestamp'], y=exit_trades['Equity'], mode='lines+markers', name='Portfolio Value'))
                    fig.update_layout(title_text='Portfolio Growth Over Time', template='plotly_dark', height=350)
                    # Remove key to let Streamlit auto-generate unique IDs
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Waiting for the first closed trade to plot the curve.")
            else:
                st.info("No trade data available to plot the curve.")
        
        # --- Live Open Positions ---
        with st.container(border=True):
                st.markdown("### 🟢 Live Open Positions")
                open_positions_df = format_open_positions(open_positions_raw)
                if not open_positions_df.empty:
                    # Format currency columns manually to avoid jinja2 dependency issue
                    df_display = open_positions_df.copy()
                    for col in ['Entry Price', 'SL', 'Target']:
                        if col in df_display.columns:
                            df_display[col] = df_display[col].apply(lambda x: f'₹{x:.2f}' if pd.notnull(x) else '')
                    st.dataframe(df_display, use_container_width=True)
                else:
                    st.info("No open positions.")

        with col2_data:
            # --- Detailed Strategy Performance ---
            with st.container(border=True):
                st.markdown("### 🧠 Strategy Analytics")
                strategy_metrics = calculate_strategy_metrics(trade_log)
                
                summary_df = pd.DataFrame.from_dict(state, orient='index')
                if not strategy_metrics.empty:
                    summary_df = summary_df.join(strategy_metrics)
                
                # Format columns manually to avoid jinja2 dependency issue
                df_display = summary_df.copy()
                format_mapping = {
                    'initial_capital': lambda x: f'₹{x:,.2f}' if pd.notnull(x) else '',
                    'trading_capital': lambda x: f'₹{x:,.2f}' if pd.notnull(x) else '',
                    'banked_profit': lambda x: f'₹{x:,.2f}' if pd.notnull(x) else '',
                    'total_charges': lambda x: f'₹{x:,.2f}' if pd.notnull(x) else '',
                    'win_rate_pct': lambda x: f'{x:.2f}%' if pd.notnull(x) else '',
                    'total_pnl': lambda x: f'₹{x:,.2f}' if pd.notnull(x) else '',
                    'avg_pnl_per_trade': lambda x: f'₹{x:,.2f}' if pd.notnull(x) else ''
                }
                for col, formatter in format_mapping.items():
                    if col in df_display.columns:
                        df_display[col] = df_display[col].apply(formatter)
                        
                st.dataframe(df_display, use_container_width=True)

            # --- Full Trade History ---
            with st.container(border=True):
                st.markdown("### 📜 Trade History")
                if not trade_log.empty:
                    display_log = trade_log.rename(columns={'strategy_name': 'Strategy', 'symbol': 'Symbol', 'action': 'Action', 'price': 'Price', 'quantity': 'Quantity', 'details': 'Details', 'timestamp': 'Timestamp'})
                    st.dataframe(display_log.sort_values(by="Timestamp", ascending=False), use_container_width=True, height=300)
                else:
                    st.info("No trades logged yet.")
    
# --- Live System Logs ---
with logs_placeholder.container(border=True):
    st.markdown("### 💻 Live System Logs")
    st.code(live_logs, language='log', line_numbers=True)

# Add a refresh button for manual updates
if st.button("🔄 Refresh Data", type="primary"):
    st.rerun()

# Show last refresh time
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
