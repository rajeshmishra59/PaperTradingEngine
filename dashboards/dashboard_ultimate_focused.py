# 🚀 ULTIMATE Focused Trading Dashboard - Best of Both Worlds
# Combines focused active strategies with vibrant visual design

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
    page_title="🚀 Ultimate Active Trading Center", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🌈 ULTIMATE VIBRANT STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    
    /* Futuristic main styling */
    .main > div {
        padding-top: 0.5rem;
        font-family: 'Orbitron', monospace;
    }
    
    /* Neon gradient cards with animation */
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
        animation: float 6s ease-in-out infinite;
    }
    
    .neon-card:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 12px 40px rgba(31, 38, 135, 0.5);
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    /* Profit glow effect with pulsing */
    .profit-glow {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 0 30px rgba(56, 239, 125, 0.5);
        color: white;
        text-align: center;
        animation: profit-pulse 2s ease-in-out infinite alternate;
        border: 2px solid rgba(56, 239, 125, 0.6);
    }
    
    @keyframes profit-pulse {
        from { 
            box-shadow: 0 0 20px rgba(56, 239, 125, 0.3);
            transform: scale(1);
        }
        to { 
            box-shadow: 0 0 40px rgba(56, 239, 125, 0.8);
            transform: scale(1.05);
        }
    }
    
    /* Loss alert effect with warning pulse */
    .loss-alert {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 0 30px rgba(255, 75, 43, 0.5);
        color: white;
        text-align: center;
        animation: loss-pulse 2s ease-in-out infinite alternate;
        border: 2px solid rgba(255, 75, 43, 0.6);
    }
    
    @keyframes loss-pulse {
        from { 
            box-shadow: 0 0 20px rgba(255, 75, 43, 0.3);
            transform: scale(1);
        }
        to { 
            box-shadow: 0 0 40px rgba(255, 75, 43, 0.8);
            transform: scale(1.05);
        }
    }
    
    /* Live status indicators with extreme glow */
    .status-live {
        display: inline-block;
        padding: 0.5rem 1rem;
        background: linear-gradient(45deg, #00ff88, #00cc6a);
        border-radius: 25px;
        color: black;
        font-weight: bold;
        animation: live-pulse 1.5s infinite;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.8);
        text-shadow: 0 0 10px rgba(0, 0, 0, 0.8);
    }
    
    @keyframes live-pulse {
        0% { transform: scale(1); box-shadow: 0 0 20px rgba(0, 255, 136, 0.8); }
        50% { transform: scale(1.1); box-shadow: 0 0 30px rgba(0, 255, 136, 1); }
        100% { transform: scale(1); box-shadow: 0 0 20px rgba(0, 255, 136, 0.8); }
    }
    
    .status-offline {
        display: inline-block;
        padding: 0.5rem 1rem;
        background: linear-gradient(45deg, #ff4b4b, #cc0000);
        border-radius: 25px;
        color: white;
        font-weight: bold;
        animation: warning-blink 2s infinite;
    }
    
    @keyframes warning-blink {
        0%, 50% { opacity: 1; }
        25%, 75% { opacity: 0.5; }
    }
    
    /* Ultimate header with rainbow gradient */
    .main-header {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%, #4facfe 100%);
        background-size: 400% 400%;
        animation: rainbow-gradient 3s ease infinite;
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        font-family: 'Orbitron', monospace;
        box-shadow: 0 10px 40px rgba(31, 38, 135, 0.6);
    }
    
    @keyframes rainbow-gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Strategy section with neon borders */
    .strategy-section {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        padding: 2rem;
        border-radius: 20px;
        margin: 2rem 0;
        border: 2px solid;
        border-image: linear-gradient(45deg, #667eea, #764ba2, #f093fb) 1;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.3);
        backdrop-filter: blur(10px);
    }
    
    /* Metric values with glow */
    .metric-value {
        font-size: 2.5rem;
        font-weight: 900;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3), 0 0 10px rgba(255,255,255,0.5);
        animation: glow-text 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow-text {
        from { text-shadow: 2px 2px 4px rgba(0,0,0,0.3), 0 0 10px rgba(255,255,255,0.5); }
        to { text-shadow: 2px 2px 4px rgba(0,0,0,0.3), 0 0 20px rgba(255,255,255,0.8); }
    }
    
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Tab styling with neon effects */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        font-weight: bold;
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Data tables with neon glow */
    .dataframe {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
        border: 1px solid rgba(102, 126, 234, 0.5);
    }
    
    /* Position cards */
    .position-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        border-left: 4px solid #00ff88;
        backdrop-filter: blur(5px);
    }
    
    /* Unrealized P&L highlight */
    .unrealized-pnl {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        font-size: 1.2rem;
        font-weight: bold;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Remove streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: bold;
        transition: all 0.3s ease;
        font-family: 'Orbitron', monospace;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# --- 🔧 DATA FUNCTIONS (Same as focused version) ---

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

@st.cache_data(ttl=3)
def load_active_strategies():
    """Load only active strategies with positions or recent activity"""
    try:
        db_manager = DatabaseManager()
        
        state = db_manager.load_full_portfolio_state()
        trade_log = db_manager.load_all_trades()
        open_positions_raw = db_manager.load_all_open_positions()
        
        active_strategies = set()
        
        # 1. Strategies with open positions
        if open_positions_raw:
            active_strategies.update(open_positions_raw.keys())
        
        # 2. Strategies with recent activity (last 24 hours)
        if not trade_log.empty:
            trade_log['timestamp'] = pd.to_datetime(trade_log['timestamp'])
            ist = pytz.timezone('Asia/Kolkata')
            recent_cutoff = datetime.now(ist) - timedelta(hours=24)
            recent_cutoff = recent_cutoff.astimezone(pytz.UTC).replace(tzinfo=None)
            
            trade_log['timestamp_naive'] = trade_log['timestamp'].dt.tz_localize(None)
            recent_trades = trade_log[trade_log['timestamp_naive'] > recent_cutoff]
            if not recent_trades.empty:
                active_strategies.update(recent_trades['strategy_name'].unique())
        
        # 3. Strategies with actual trading capital changes
        if state:
            for strategy, data in state.items():
                trading_capital = data.get('trading_capital', 100000)
                banked_profit = data.get('banked_profit', 0)
                if trading_capital != 100000 or banked_profit != 0:
                    active_strategies.add(strategy)
        
        filtered_state = {k: v for k, v in state.items() if k in active_strategies}
        filtered_positions = {k: v for k, v in open_positions_raw.items() if k in active_strategies}
        
        if not trade_log.empty:
            filtered_trades = trade_log[trade_log['strategy_name'].isin(active_strategies)]
        else:
            filtered_trades = pd.DataFrame()
        
        return filtered_state, filtered_trades, filtered_positions, list(active_strategies), None
        
    except Exception as e:
        return {}, pd.DataFrame(), {}, [], str(e)

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
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'total_pnl': total_pnl,
        'win_rate': win_rate
    }

def create_strategy_pnl_chart(trade_log_df, strategy_name):
    """Create vibrant P&L chart for specific strategy"""
    strategy_trades = trade_log_df[trade_log_df['strategy_name'] == strategy_name]
    exit_trades = strategy_trades[strategy_trades['action'].str.contains('EXIT', na=False)].copy()
    
    if exit_trades.empty:
        fig = go.Figure()
        fig.add_annotation(text=f"🚀 No completed trades for {strategy_name} yet!", 
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
        subplot_titles=[f'📈 {strategy_name} - Cumulative Performance', '📊 Individual Trade Results'],
        vertical_spacing=0.1
    )
    
    # Cumulative P&L with gradient
    line_color = '#00ff88' if exit_trades['Cumulative_PnL'].iloc[-1] >= 0 else '#ff4b4b'
    
    fig.add_trace(go.Scatter(
        x=exit_trades['timestamp'],
        y=exit_trades['Cumulative_PnL'],
        mode='lines+markers',
        name='Cumulative P&L',
        line=dict(color=line_color, width=4),
        marker=dict(size=8, color=line_color, line=dict(width=2, color='white')),
        fill='tonexty',
        fillcolor=f'rgba({", ".join(str(int(line_color[i:i+2], 16)) for i in (1, 3, 5))}, 0.2)',
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
        title=f'🚀 {strategy_name} Performance Analytics',
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='Orbitron'),
        showlegend=True
    )
    
    return fig

# --- 🚀 ULTIMATE MAIN DASHBOARD ---

# Header with animated status
bot_running, market_open, current_time = get_system_status()

st.markdown(f"""
<div class="main-header">
    <h1>⚡ ULTIMATE ACTIVE TRADING CONTROL CENTER ⚡</h1>
    <h3>🎯 Live Strategies • Real-time Performance • AI Analytics</h3>
    <div style="display: flex; justify-content: space-around; margin-top: 1.5rem; font-size: 1.1rem;">
        <div>Bot: {'🟢 LIVE' if bot_running else '🔴 OFFLINE'}</div>
        <div>Market: {'🟢 OPEN' if market_open else '🔴 CLOSED'}</div>
        <div>Time: {current_time}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Status indicators
col1, col2, col3, col4 = st.columns(4)

with col1:
    status_class = "status-live" if bot_running else "status-offline"
    status_text = "🟢 LIVE" if bot_running else "🔴 OFFLINE"
    st.markdown(f'<div class="{status_class}">{status_text}</div>', unsafe_allow_html=True)

with col2:
    market_status = "🟢 OPEN" if market_open else "🔴 CLOSED"
    st.markdown(f"**Market:** {market_status}")

with col3:
    st.markdown(f"**Time:** {current_time}")

with col4:
    st.markdown("**Status:** 💓 ACTIVE" if bot_running else "**Status:** ⚠️ STALE")

# Load active strategies
with st.spinner("🔍 Loading active strategies..."):
    state, trade_log, open_positions, active_strategies, error = load_active_strategies()

if error:
    st.error(f"❌ Error: {error}")
    st.stop()

if not active_strategies:
    st.warning("⚠️ No active strategies found!")
    st.stop()

st.success(f"✅ Found {len(active_strategies)} active strategies")

# Display each strategy with ultimate visuals
for i, strategy_name in enumerate(active_strategies):
    
    st.markdown(f"""
    <div class="strategy-section">
        <h2 style="text-align: center; color: white; font-family: 'Orbitron', monospace;">
            🎯 {strategy_name}
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Get strategy data
    metrics = calculate_strategy_metrics(trade_log, strategy_name)
    strategy_state = state.get(strategy_name, {})
    strategy_positions = open_positions.get(strategy_name, {})
    
    # Ultimate metric cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        capital = strategy_state.get('trading_capital', 0)
        card_class = "profit-glow" if capital > 100000 else "loss-alert" if capital < 100000 else "neon-card"
        st.markdown(f"""
        <div class="{card_class}">
            <p class="metric-value">₹{capital:,.0f}</p>
            <p class="metric-label">Trading Capital</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        profit = strategy_state.get('banked_profit', 0)
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
    
    # Ultimate tabs
    tab1, tab2, tab3 = st.tabs(["📊 Performance Chart", "📋 Live Positions", "📈 Recent Trades"])
    
    with tab1:
        if metrics.get('total_trades', 0) > 0:
            fig = create_strategy_pnl_chart(trade_log, strategy_name)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("🚀 No completed trades yet - Strategy warming up!")
    
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
                
                pnl_color = "🟢" if unrealized_pnl >= 0 else "🔴"
                change_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                
                position_data.append({
                    "Symbol": symbol,
                    "Action": action,
                    "Qty": quantity,
                    "Entry": f"₹{entry_price:.2f}",
                    "Current": f"₹{current_price:.2f}",
                    "P&L": f"{pnl_color} ₹{unrealized_pnl:.2f}",
                    "Change%": f"{change_pct:+.2f}%"
                })
            
            if position_data:
                # Ultimate unrealized P&L display
                pnl_class = "profit-glow" if total_unrealized >= 0 else "loss-alert"
                st.markdown(f"""
                <div class="{pnl_class}">
                    <h3>💰 Total Unrealized P&L: ₹{total_unrealized:,.2f}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                df_positions = pd.DataFrame(position_data)
                st.dataframe(df_positions, use_container_width=True, hide_index=True)
        else:
            st.info("📋 No open positions")
    
    with tab3:
        strategy_recent_trades = trade_log[trade_log['strategy_name'] == strategy_name].tail(10)
        if not strategy_recent_trades.empty:
            display_trades = strategy_recent_trades[['timestamp', 'symbol', 'action', 'price', 'quantity']].copy()
            display_trades['timestamp'] = pd.to_datetime(display_trades['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(display_trades, use_container_width=True, hide_index=True)
        else:
            st.info("📈 No recent trades")
    
    st.markdown("---")

# Ultimate summary
st.markdown("## 🌟 Active Strategies Command Center")
total_active = len(active_strategies)
total_positions = sum(len(positions) for positions in open_positions.values())
total_capital = sum(data.get('trading_capital', 0) for data in state.values())

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="neon-card">
        <p class="metric-value">{total_active}</p>
        <p class="metric-label">🎯 Active Strategies</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="neon-card">
        <p class="metric-value">{total_positions}</p>
        <p class="metric-label">📋 Total Positions</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="neon-card">
        <p class="metric-value">₹{total_capital:,.0f}</p>
        <p class="metric-label">💰 Total Capital</p>
    </div>
    """, unsafe_allow_html=True)

# Sidebar controls
st.sidebar.markdown("## ⚙️ Control Panel")
auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh", value=False)
refresh_interval = st.sidebar.selectbox("Refresh Rate", [3, 5, 10, 30], index=1)

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

if st.sidebar.button("🔄 Force Refresh"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(f"**🕐 Last Updated:** {datetime.now().strftime('%H:%M:%S')}")
st.sidebar.markdown(f"**🎯 Active Strategies:**")
for strategy in active_strategies:
    st.sidebar.markdown(f"• {strategy}")
