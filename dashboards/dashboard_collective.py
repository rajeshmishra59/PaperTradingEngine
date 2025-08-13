# 🚀 COLLECTIVE Trading Dashboard - All Strategies with Selection
# Shows all strategies collectively with dropdown selection for detailed view

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
    page_title="🚀 Collective Trading Dashboard", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🌈 VIBRANT STYLING ---
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
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .neon-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(31, 38, 135, 0.5);
    }
    
    .profit-glow {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 0 30px rgba(56, 239, 125, 0.5);
        color: white;
        text-align: center;
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { box-shadow: 0 0 20px rgba(56, 239, 125, 0.3); }
        to { box-shadow: 0 0 40px rgba(56, 239, 125, 0.8); }
    }
    
    .loss-alert {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 0 30px rgba(255, 75, 43, 0.5);
        color: white;
        text-align: center;
        animation: pulse-red 2s ease-in-out infinite alternate;
    }
    
    @keyframes pulse-red {
        from { box-shadow: 0 0 20px rgba(255, 75, 43, 0.3); }
        to { box-shadow: 0 0 40px rgba(255, 75, 43, 0.8); }
    }
    
    .status-live {
        display: inline-block;
        padding: 0.5rem 1rem;
        background: linear-gradient(45deg, #00ff88, #00cc6a);
        border-radius: 25px;
        color: black;
        font-weight: bold;
        animation: live-pulse 1.5s infinite;
    }
    
    @keyframes live-pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
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
    
    .strategy-row {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
        backdrop-filter: blur(5px);
    }
    
    .active-strategy {
        border-left: 4px solid #00ff88;
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(17, 153, 142, 0.1) 100%);
    }
    
    .inactive-strategy {
        border-left: 4px solid #ff4b4b;
        background: linear-gradient(135deg, rgba(255, 75, 75, 0.1) 0%, rgba(204, 0, 0, 0.1) 100%);
    }
</style>
""", unsafe_allow_html=True)

# --- 🔧 DATA FUNCTIONS ---

def get_system_status():
    """Get basic system status"""
    try:
        result = subprocess.run(['pgrep', '-f', 'main_papertrader'], 
                              capture_output=True, text=True)
        bot_running = len(result.stdout.strip()) > 0
        
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)
        market_open = (9, 15) <= (now_ist.hour, now_ist.minute) <= (15, 30)
        is_weekday = now_ist.weekday() < 5
        
        return bot_running, market_open and is_weekday, now_ist.strftime('%H:%M:%S IST')
    except:
        return False, False, 'N/A'

@st.cache_data(ttl=5)
def load_all_strategies():
    """Load all strategies with status indicators"""
    try:
        db_manager = DatabaseManager()
        
        state = db_manager.load_full_portfolio_state()
        trade_log = db_manager.load_all_trades()
        open_positions_raw = db_manager.load_all_open_positions()
        
        # Determine strategy status
        strategy_info = {}
        
        for strategy_name, strategy_data in state.items():
            trading_capital = strategy_data.get('trading_capital', 100000)
            banked_profit = strategy_data.get('banked_profit', 0)
            
            # Check if strategy is active
            has_positions = strategy_name in open_positions_raw
            has_modified_capital = trading_capital != 100000 or banked_profit != 0
            
            # Check recent activity
            has_recent_activity = False
            if not trade_log.empty:
                strategy_trades = trade_log[trade_log['strategy_name'] == strategy_name]
                if not strategy_trades.empty:
                    strategy_trades['timestamp'] = pd.to_datetime(strategy_trades['timestamp'])
                    ist = pytz.timezone('Asia/Kolkata')
                    recent_cutoff = datetime.now(ist) - timedelta(hours=24)
                    recent_cutoff = recent_cutoff.astimezone(pytz.UTC).replace(tzinfo=None)
                    
                    strategy_trades['timestamp_naive'] = strategy_trades['timestamp'].dt.tz_localize(None)
                    recent_trades = strategy_trades[strategy_trades['timestamp_naive'] > recent_cutoff]
                    has_recent_activity = not recent_trades.empty
            
            # Determine status
            is_active = has_positions or has_modified_capital or has_recent_activity
            
            strategy_info[strategy_name] = {
                'data': strategy_data,
                'is_active': is_active,
                'has_positions': has_positions,
                'has_recent_activity': has_recent_activity,
                'positions_count': len(open_positions_raw.get(strategy_name, {}))
            }
        
        return state, trade_log, open_positions_raw, strategy_info, None
        
    except Exception as e:
        return {}, pd.DataFrame(), {}, {}, str(e)

def parse_pnl(detail_str: str) -> float:
    """Extract PnL from details string"""
    if not isinstance(detail_str, str):
        return 0.0
    match = re.search(r"PnL:\s*(-?[\d,]+\.\d{2})", detail_str)
    return float(match.group(1).replace(",", "")) if match else 0.0

def calculate_strategy_metrics(trade_log_df, strategy_name):
    """Calculate metrics for specific strategy"""
    if trade_log_df.empty:
        return {}
    
    strategy_trades = trade_log_df[trade_log_df['strategy_name'] == strategy_name]
    exit_trades = strategy_trades[strategy_trades['action'].str.contains('EXIT', na=False)].copy()
    
    if exit_trades.empty:
        return {'total_trades': 0, 'total_pnl': 0, 'win_rate': 0}
    
    exit_trades['PnL'] = exit_trades['details'].apply(parse_pnl)
    
    total_trades = len(exit_trades)
    winning_trades = len(exit_trades[exit_trades['PnL'] > 0])
    total_pnl = exit_trades['PnL'].sum()
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    avg_win = exit_trades[exit_trades['PnL'] > 0]['PnL'].mean() if winning_trades > 0 else 0
    avg_loss = exit_trades[exit_trades['PnL'] <= 0]['PnL'].mean() if (total_trades - winning_trades) > 0 else 0
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss
    }

def create_collective_overview_chart(trade_log_df, strategy_info):
    """Create overview chart for all strategies"""
    fig = go.Figure()
    
    # Strategy performance comparison
    strategies = []
    total_pnls = []
    win_rates = []
    colors = []
    
    for strategy_name in strategy_info.keys():
        metrics = calculate_strategy_metrics(trade_log_df, strategy_name)
        total_pnl = metrics.get('total_pnl', 0)
        win_rate = metrics.get('win_rate', 0)
        
        strategies.append(strategy_name)
        total_pnls.append(total_pnl)
        win_rates.append(win_rate)
        
        # Color based on performance
        if total_pnl > 0:
            colors.append('#00ff88')
        elif total_pnl < 0:
            colors.append('#ff4b4b')
        else:
            colors.append('#667eea')
    
    fig.add_trace(go.Bar(
        x=strategies,
        y=total_pnls,
        name='Total P&L',
        marker_color=colors,
        text=[f"₹{pnl:,.0f}" for pnl in total_pnls],
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>P&L: ₹%{y:,.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title='🚀 Strategy Performance Overview',
        xaxis_title='Strategies',
        yaxis_title='Total P&L (₹)',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='Orbitron'),
        height=400
    )
    
    return fig

def create_strategy_detail_chart(trade_log_df, strategy_name):
    """Create detailed chart for selected strategy"""
    strategy_trades = trade_log_df[trade_log_df['strategy_name'] == strategy_name]
    exit_trades = strategy_trades[strategy_trades['action'].str.contains('EXIT', na=False)].copy()
    
    if exit_trades.empty:
        fig = go.Figure()
        fig.add_annotation(text=f"No completed trades for {strategy_name}", 
                          xref="paper", yref="paper", x=0.5, y=0.5, 
                          showarrow=False, font_size=18, font_color="white")
        fig.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        return fig
    
    exit_trades['PnL'] = exit_trades['details'].apply(parse_pnl)
    exit_trades['timestamp'] = pd.to_datetime(exit_trades['timestamp'])
    exit_trades = exit_trades.sort_values('timestamp')
    exit_trades['Cumulative_PnL'] = exit_trades['PnL'].cumsum()
    
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.7, 0.3],
        subplot_titles=[f'📈 {strategy_name} - Cumulative Performance', '📊 Individual Trades'],
        vertical_spacing=0.1
    )
    
    # Cumulative P&L
    line_color = '#00ff88' if exit_trades['Cumulative_PnL'].iloc[-1] >= 0 else '#ff4b4b'
    
    fig.add_trace(go.Scatter(
        x=exit_trades['timestamp'],
        y=exit_trades['Cumulative_PnL'],
        mode='lines+markers',
        name='Cumulative P&L',
        line=dict(color=line_color, width=4),
        marker=dict(size=8, color=line_color),
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
        title=f'🎯 {strategy_name} Detailed Analytics',
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='Orbitron'),
        showlegend=False
    )
    
    return fig

# --- 🚀 MAIN DASHBOARD ---

# Header
bot_running, market_open, current_time = get_system_status()

st.markdown(f"""
<div class="main-header">
    <h1>⚡ COLLECTIVE TRADING STRATEGIES DASHBOARD ⚡</h1>
    <h3>🎯 All Strategies • Selective Analysis • Real-time Monitoring</h3>
    <div style="display: flex; justify-content: space-around; margin-top: 1.5rem;">
        <div>Bot: {'🟢 LIVE' if bot_running else '🔴 OFFLINE'}</div>
        <div>Market: {'🟢 OPEN' if market_open else '🔴 CLOSED'}</div>
        <div>Time: {current_time}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Load all strategies
with st.spinner("🔍 Loading all strategies..."):
    state, trade_log, open_positions, strategy_info, error = load_all_strategies()

if error:
    st.error(f"❌ Error: {error}")
    st.stop()

if not strategy_info:
    st.warning("⚠️ No strategies found!")
    st.stop()

# Strategy selection sidebar
st.sidebar.markdown("## 🎯 Strategy Selection")
selected_strategy = st.sidebar.selectbox(
    "Select Strategy for Detailed View:",
    ["📊 Overview (All Strategies)"] + list(strategy_info.keys())
)

# Collective overview section
st.markdown("## 📊 All Strategies Overview")

# Summary metrics
active_count = sum(1 for info in strategy_info.values() if info['is_active'])
total_positions = sum(info['positions_count'] for info in strategy_info.values())
total_capital = sum(data.get('trading_capital', 0) for data in state.values())

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="neon-card">
        <p class="metric-value">{len(strategy_info)}</p>
        <p class="metric-label">Total Strategies</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="profit-glow">
        <p class="metric-value">{active_count}</p>
        <p class="metric-label">Active Strategies</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="neon-card">
        <p class="metric-value">{total_positions}</p>
        <p class="metric-label">Total Positions</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="neon-card">
        <p class="metric-value">₹{total_capital:,.0f}</p>
        <p class="metric-label">Total Capital</p>
    </div>
    """, unsafe_allow_html=True)

# Strategy list with status
st.markdown("### 📋 All Strategies Status")

for strategy_name, info in strategy_info.items():
    metrics = calculate_strategy_metrics(trade_log, strategy_name)
    
    status_class = "active-strategy" if info['is_active'] else "inactive-strategy"
    status_text = "🟢 ACTIVE" if info['is_active'] else "🔴 INACTIVE"
    
    col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div class="strategy-row {status_class}">
            <strong>{strategy_name}</strong><br>
            <small>{status_text}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        capital = info['data'].get('trading_capital', 0)
        st.metric("Capital", f"₹{capital:,.0f}")
    
    with col3:
        profit = info['data'].get('banked_profit', 0)
        st.metric("Profit", f"₹{profit:,.2f}")
    
    with col4:
        total_pnl = metrics.get('total_pnl', 0)
        st.metric("Total P&L", f"₹{total_pnl:,.0f}")
    
    with col5:
        win_rate = metrics.get('win_rate', 0)
        st.metric("Win Rate", f"{win_rate:.1f}%")
    
    with col6:
        positions = info['positions_count']
        st.metric("Positions", positions)

# Main content area
if selected_strategy == "📊 Overview (All Strategies)":
    st.markdown("## 📈 Collective Performance Analysis")
    
    # Overview chart
    fig_overview = create_collective_overview_chart(trade_log, strategy_info)
    st.plotly_chart(fig_overview, use_container_width=True)
    
    # Active strategies summary
    active_strategies = [name for name, info in strategy_info.items() if info['is_active']]
    
    if active_strategies:
        st.markdown("### 🎯 Currently Active Strategies")
        
        for strategy in active_strategies:
            with st.expander(f"📊 {strategy} - Quick View"):
                col1, col2, col3 = st.columns(3)
                
                metrics = calculate_strategy_metrics(trade_log, strategy)
                strategy_data = strategy_info[strategy]['data']
                
                with col1:
                    st.metric("Trading Capital", f"₹{strategy_data.get('trading_capital', 0):,.0f}")
                    st.metric("Banked Profit", f"₹{strategy_data.get('banked_profit', 0):,.2f}")
                
                with col2:
                    st.metric("Total Trades", metrics.get('total_trades', 0))
                    st.metric("Win Rate", f"{metrics.get('win_rate', 0):.1f}%")
                
                with col3:
                    st.metric("Total P&L", f"₹{metrics.get('total_pnl', 0):,.2f}")
                    st.metric("Open Positions", strategy_info[strategy]['positions_count'])

else:
    # Selected strategy detailed view
    st.markdown(f"## 🎯 {selected_strategy} - Detailed Analysis")
    
    strategy_data = strategy_info[selected_strategy]['data']
    strategy_positions = open_positions.get(selected_strategy, {})
    metrics = calculate_strategy_metrics(trade_log, selected_strategy)
    
    # Strategy metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        capital = strategy_data.get('trading_capital', 0)
        card_class = "profit-glow" if capital > 100000 else "loss-alert" if capital < 100000 else "neon-card"
        st.markdown(f"""
        <div class="{card_class}">
            <p class="metric-value">₹{capital:,.0f}</p>
            <p class="metric-label">Trading Capital</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        profit = strategy_data.get('banked_profit', 0)
        card_class = "profit-glow" if profit > 0 else "loss-alert" if profit < 0 else "neon-card"
        st.markdown(f"""
        <div class="{card_class}">
            <p class="metric-value">₹{profit:,.2f}</p>
            <p class="metric-label">Banked Profit</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_pnl = metrics.get('total_pnl', 0)
        card_class = "profit-glow" if total_pnl > 0 else "loss-alert" if total_pnl < 0 else "neon-card"
        st.markdown(f"""
        <div class="{card_class}">
            <p class="metric-value">₹{total_pnl:,.0f}</p>
            <p class="metric-label">Total P&L</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        win_rate = metrics.get('win_rate', 0)
        card_class = "profit-glow" if win_rate >= 60 else "loss-alert" if win_rate < 40 else "neon-card"
        st.markdown(f"""
        <div class="{card_class}">
            <p class="metric-value">{win_rate:.1f}%</p>
            <p class="metric-label">Win Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        total_trades = metrics.get('total_trades', 0)
        st.markdown(f"""
        <div class="neon-card">
            <p class="metric-value">{total_trades}</p>
            <p class="metric-label">Total Trades</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Strategy tabs
    tab1, tab2, tab3 = st.tabs(["📊 Performance Chart", "📋 Open Positions", "📈 Recent Trades"])
    
    with tab1:
        if metrics.get('total_trades', 0) > 0:
            fig = create_strategy_detail_chart(trade_log, selected_strategy)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 No completed trades yet")
    
    with tab2:
        if strategy_positions:
            position_data = []
            total_unrealized = 0
            
            for symbol, details in strategy_positions.items():
                entry_price = details.get('entry_price', 0)
                current_price = details.get('current_price', entry_price)
                quantity = details.get('quantity', 0)
                action = details.get('action', '')
                
                if action == 'LONG':
                    unrealized_pnl = (current_price - entry_price) * quantity
                else:
                    unrealized_pnl = (entry_price - current_price) * quantity
                
                total_unrealized += unrealized_pnl
                
                position_data.append({
                    "Symbol": symbol,
                    "Action": action,
                    "Qty": quantity,
                    "Entry": f"₹{entry_price:.2f}",
                    "Current": f"₹{current_price:.2f}",
                    "Unrealized P&L": f"₹{unrealized_pnl:.2f}",
                    "% Change": f"{((current_price - entry_price) / entry_price * 100):.2f}%"
                })
            
            if position_data:
                pnl_color = "profit-glow" if total_unrealized >= 0 else "loss-alert"
                st.markdown(f"""
                <div class="{pnl_color}">
                    <h3>Total Unrealized P&L: ₹{total_unrealized:,.2f}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                df_positions = pd.DataFrame(position_data)
                st.dataframe(df_positions, use_container_width=True, hide_index=True)
        else:
            st.info("📋 No open positions")
    
    with tab3:
        strategy_trades = trade_log[trade_log['strategy_name'] == selected_strategy].tail(10)
        if not strategy_trades.empty:
            display_trades = strategy_trades[['timestamp', 'symbol', 'action', 'price', 'quantity']].copy()
            display_trades['timestamp'] = pd.to_datetime(display_trades['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(display_trades, use_container_width=True, hide_index=True)
        else:
            st.info("📈 No recent trades")

# Sidebar controls
st.sidebar.markdown("---")
st.sidebar.markdown("## ⚙️ Controls")
auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh", value=False)
refresh_interval = st.sidebar.selectbox("Refresh Rate", [5, 10, 30, 60], index=1)

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

if st.sidebar.button("🔄 Force Refresh"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(f"**🕐 Last Updated:** {datetime.now().strftime('%H:%M:%S')}")
st.sidebar.markdown(f"**📊 Total Strategies:** {len(strategy_info)}")
st.sidebar.markdown(f"**🎯 Active:** {active_count}")
st.sidebar.markdown(f"**💼 Total Positions:** {total_positions}")
