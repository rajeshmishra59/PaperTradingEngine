# 🚀 FIXED Ultimate AI Trading Dashboard
# Simplified version without complex imports to ensure data displays

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
import os
import re
import json
import numpy as np
from datetime import datetime, timedelta
from database_manager import DatabaseManager
import pytz
import subprocess

# --- 🎨 PAGE CONFIGURATION ---
st.set_page_config(
    page_title="🚀 Ultimate AI Trading Control Center", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🌈 SIMPLIFIED STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    
    .main > div {
        padding-top: 0.5rem;
        font-family: 'Orbitron', monospace;
    }
    
    .neon-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .profit-glow {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 0 30px rgba(56, 239, 125, 0.5);
        color: white;
        text-align: center;
    }
    
    .loss-alert {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 0 30px rgba(255, 75, 43, 0.5);
        color: white;
        text-align: center;
    }
    
    .status-live {
        display: inline-block;
        padding: 0.5rem 1rem;
        background: linear-gradient(45deg, #00ff88, #00cc6a);
        border-radius: 25px;
        color: black;
        font-weight: bold;
    }
    
    .status-offline {
        display: inline-block;
        padding: 0.5rem 1rem;
        background: linear-gradient(45deg, #ff4b4b, #cc0000);
        border-radius: 25px;
        color: white;
        font-weight: bold;
    }
    
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        font-family: 'Orbitron', monospace;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 900;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 🔧 SIMPLIFIED DATA FUNCTIONS ---

def get_bot_status():
    """Simple bot status check"""
    try:
        result = subprocess.run(['pgrep', '-f', 'main_papertrader'], 
                              capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except:
        return False

def get_market_status():
    """Simple market status check"""
    try:
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)
        market_open = (9, 15) <= (now_ist.hour, now_ist.minute) <= (15, 30)
        is_weekday = now_ist.weekday() < 5
        return market_open and is_weekday, now_ist.strftime('%H:%M:%S IST')
    except:
        return False, 'N/A'

@st.cache_data(ttl=5)
def load_trading_data():
    """Load all trading data"""
    try:
        db_manager = DatabaseManager()
        
        # Load data
        state = db_manager.load_full_portfolio_state()
        trade_log = db_manager.load_all_trades()
        open_positions_raw = db_manager.load_all_open_positions()
        
        return state, trade_log, open_positions_raw, None
    except Exception as e:
        return {}, pd.DataFrame(), {}, str(e)

def parse_pnl(detail_str: str) -> float:
    """Extract PnL from details string"""
    if not isinstance(detail_str, str):
        return 0.0
    match = re.search(r"PnL:\s*(-?[\d,]+\.\d{2})", detail_str)
    return float(match.group(1).replace(",", "")) if match else 0.0

def calculate_metrics(trade_log_df):
    """Calculate comprehensive trading metrics"""
    if trade_log_df.empty:
        return {}
    
    exit_trades = trade_log_df[trade_log_df['action'].str.contains('EXIT', na=False)].copy()
    if exit_trades.empty:
        return {}
    
    exit_trades['PnL'] = exit_trades['details'].apply(parse_pnl)
    
    total_trades = len(exit_trades)
    winning_trades = len(exit_trades[exit_trades['PnL'] > 0])
    total_pnl = exit_trades['PnL'].sum()
    avg_win = exit_trades[exit_trades['PnL'] > 0]['PnL'].mean() if winning_trades > 0 else 0
    avg_loss = exit_trades[exit_trades['PnL'] <= 0]['PnL'].mean() if (total_trades - winning_trades) > 0 else 0
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    profit_factor = abs(avg_win * winning_trades / (avg_loss * (total_trades - winning_trades))) if avg_loss != 0 else 0
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor
    }

def create_pnl_chart(trade_log_df):
    """Create P&L chart"""
    if trade_log_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No trading data available", 
                          xref="paper", yref="paper", x=0.5, y=0.5, 
                          showarrow=False, font_size=20)
        return fig
    
    exit_trades = trade_log_df[trade_log_df['action'].str.contains('EXIT', na=False)].copy()
    if exit_trades.empty:
        fig = go.Figure()
        fig.add_annotation(text="No completed trades yet", 
                          xref="paper", yref="paper", x=0.5, y=0.5, 
                          showarrow=False, font_size=20)
        return fig
    
    exit_trades['PnL'] = exit_trades['details'].apply(parse_pnl)
    exit_trades['timestamp'] = pd.to_datetime(exit_trades['timestamp'])
    exit_trades = exit_trades.sort_values('timestamp')
    exit_trades['Cumulative_PnL'] = exit_trades['PnL'].cumsum()
    
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.7, 0.3],
        subplot_titles=['📈 Cumulative P&L Performance', '📊 Individual Trade Results'],
        vertical_spacing=0.1
    )
    
    # Cumulative P&L
    fig.add_trace(go.Scatter(
        x=exit_trades['timestamp'],
        y=exit_trades['Cumulative_PnL'],
        mode='lines+markers',
        name='Cumulative P&L',
        line=dict(color='#00ff88', width=4),
        marker=dict(size=8, color='#00ff88'),
        hovertemplate='<b>₹%{y:,.2f}</b><br>%{x}<extra></extra>'
    ), row=1, col=1)
    
    # Individual trades
    colors = ['#ff4b4b' if pnl < 0 else '#00ff88' for pnl in exit_trades['PnL']]
    
    fig.add_trace(go.Bar(
        x=exit_trades['timestamp'],
        y=exit_trades['PnL'],
        name='Trade P&L',
        marker_color=colors,
        opacity=0.8,
        hovertemplate='<b>₹%{y:,.2f}</b><br>%{x}<extra></extra>'
    ), row=2, col=1)
    
    fig.update_layout(
        title='🚀 P&L Analytics Dashboard',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        showlegend=True,
        height=700
    )
    
    return fig

# --- 🚀 MAIN DASHBOARD ---

# Header
bot_running = get_bot_status()
market_open, current_time = get_market_status()

st.markdown(f"""
<div class="main-header">
    <h1>⚡ ULTIMATE AI TRADING CONTROL CENTER ⚡</h1>
    <h3>Advanced Analytics • Real-time Monitoring • AI Insights</h3>
</div>
""", unsafe_allow_html=True)

# Status bar
col1, col2, col3, col4 = st.columns(4)

with col1:
    status_class = "status-live" if bot_running else "status-offline"
    status_text = "🟢 LIVE" if bot_running else "🔴 OFFLINE"
    st.markdown(f'<div class="{status_class}">{status_text}</div>', unsafe_allow_html=True)

with col2:
    market_status_text = "🟢 OPEN" if market_open else "🔴 CLOSED"
    st.markdown(f"**Market:** {market_status_text}")

with col3:
    st.markdown(f"**Time:** {current_time}")

with col4:
    st.markdown("**Status:** 💓 ACTIVE" if bot_running else "**Status:** ⚠️ STALE")

# Load data
st.markdown("## 🔄 Loading Trading Data...")
state, trade_log, open_positions_raw, error = load_trading_data()

if error:
    st.error(f"❌ Database Error: {error}")
    st.stop()

st.success("✅ Data loaded successfully!")

# Show data summary
st.markdown("## 📊 Data Summary")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📈 Total Trades", len(trade_log))
with col2:
    st.metric("💼 Strategies", len(state))
with col3:
    if open_positions_raw:
        total_positions = sum(len(symbols) for symbols in open_positions_raw.values())
        st.metric("📋 Open Positions", total_positions)
    else:
        st.metric("📋 Open Positions", 0)

# Calculate and show metrics
if not trade_log.empty:
    metrics = calculate_metrics(trade_log)
    
    if metrics:
        st.markdown("## 🎯 Trading Performance")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            pnl = metrics['total_pnl']
            card_class = "profit-glow" if pnl >= 0 else "loss-alert"
            st.markdown(f"""
            <div class="{card_class}">
                <p class="metric-value">₹{pnl:,.0f}</p>
                <p class="metric-label">Total P&L</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="neon-card">
                <p class="metric-value">{metrics['total_trades']}</p>
                <p class="metric-label">Total Trades</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            win_rate = metrics['win_rate']
            card_class = "profit-glow" if win_rate >= 60 else "neon-card" if win_rate >= 40 else "loss-alert"
            st.markdown(f"""
            <div class="{card_class}">
                <p class="metric-value">{win_rate:.1f}%</p>
                <p class="metric-label">Win Rate</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.metric("💰 Avg Win", f"₹{metrics['avg_win']:,.2f}")
        
        with col5:
            st.metric("💸 Avg Loss", f"₹{metrics['avg_loss']:,.2f}")

# Analytics tabs
st.markdown("## 📈 Analytics Dashboard")

tab1, tab2, tab3 = st.tabs(["📊 P&L Analytics", "📋 Live Positions", "💰 Portfolio State"])

with tab1:
    if not trade_log.empty:
        st.plotly_chart(create_pnl_chart(trade_log), use_container_width=True)
    else:
        st.info("📈 No trading data available yet")

with tab2:
    if open_positions_raw:
        positions_list = []
        total_unrealized = 0
        
        for strat, symbols in open_positions_raw.items():
            for symbol, details in symbols.items():
                entry_price = details.get('entry_price', 0)
                current_price = details.get('current_price', entry_price)
                quantity = details.get('quantity', 0)
                action = details.get('action', '')
                
                if action == 'LONG':
                    unrealized_pnl = (current_price - entry_price) * quantity
                else:
                    unrealized_pnl = (entry_price - current_price) * quantity
                
                total_unrealized += unrealized_pnl
                
                positions_list.append({
                    "Strategy": strat,
                    "Symbol": symbol,
                    "Action": action,
                    "Qty": quantity,
                    "Entry": f"₹{entry_price:.2f}",
                    "Current": f"₹{current_price:.2f}",
                    "Unrealized P&L": f"₹{unrealized_pnl:.2f}",
                    "% Change": f"{((current_price - entry_price) / entry_price * 100):.2f}%"
                })
        
        if positions_list:
            pnl_color = "profit-glow" if total_unrealized >= 0 else "loss-alert"
            st.markdown(f"""
            <div class="{pnl_color}">
                <h3>Total Unrealized P&L: ₹{total_unrealized:,.2f}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            df_positions = pd.DataFrame(positions_list)
            st.dataframe(df_positions, use_container_width=True)
        else:
            st.info("📈 No open positions")
    else:
        st.info("📈 No open positions")

with tab3:
    if state:
        portfolio_list = []
        for strategy, data in state.items():
            portfolio_list.append({
                "Strategy": strategy,
                "Initial Capital": f"₹{data.get('initial_capital', 0):,.2f}",
                "Trading Capital": f"₹{data.get('trading_capital', 0):,.2f}",
                "Banked Profit": f"₹{data.get('banked_profit', 0):,.2f}",
                "Total Charges": f"₹{data.get('total_charges', 0):,.2f}"
            })
        
        if portfolio_list:
            df_portfolio = pd.DataFrame(portfolio_list)
            st.dataframe(df_portfolio, use_container_width=True)
        else:
            st.info("💰 No portfolio data")
    else:
        st.info("💰 No portfolio data")

# Recent trades
if not trade_log.empty:
    st.markdown("## 📋 Recent Trading Activity")
    recent_trades = trade_log.tail(10)
    st.dataframe(recent_trades[['timestamp', 'strategy_name', 'symbol', 'action', 'price', 'quantity']], use_container_width=True)

# Auto refresh
if st.sidebar.checkbox("🔄 Auto Refresh", value=False):
    time.sleep(5)
    st.rerun()

# Manual refresh
if st.sidebar.button("🔄 Force Refresh"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Last Updated:** {datetime.now().strftime('%H:%M:%S')}")
