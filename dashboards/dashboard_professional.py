# 🎯 PROFESSIONAL TRADING DASHBOARD - Active Strategies Only
# Focus: Live P&L, Open Trades, Capital Curve, Drawdown Analysis

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
import json
import re
import numpy as np
from datetime import datetime, timedelta
from database_manager import DatabaseManager
import pytz
import subprocess

# --- 🎨 ULTIMATE VIBRANT STYLING ---
st.set_page_config(
    page_title="⚡ ULTIMATE ACTIVE TRADING CONTROL CENTER", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@400;500;600;700&display=swap');
    
    .main > div {
        padding-top: 0.5rem;
        font-family: 'Orbitron', 'Inter', sans-serif;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        min-height: 100vh;
    }
    
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
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
        animation: floating 3s ease-in-out infinite;
    }
    
    @keyframes floating {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    .neon-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(31, 38, 135, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    .profit-glow {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 0 30px rgba(56, 239, 125, 0.5);
        color: white;
        text-align: center;
        animation: glow-green 2s ease-in-out infinite alternate;
        border: 2px solid rgba(56, 239, 125, 0.3);
    }
    
    @keyframes glow-green {
        from { 
            box-shadow: 0 0 20px rgba(56, 239, 125, 0.3);
            border-color: rgba(56, 239, 125, 0.3);
        }
        to { 
            box-shadow: 0 0 40px rgba(56, 239, 125, 0.8);
            border-color: rgba(56, 239, 125, 0.6);
        }
    }
    
    .loss-alert {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 0 30px rgba(255, 75, 43, 0.5);
        color: white;
        text-align: center;
        animation: pulse-red 2s ease-in-out infinite alternate;
        border: 2px solid rgba(255, 75, 43, 0.3);
    }
    
    @keyframes pulse-red {
        from { 
            box-shadow: 0 0 20px rgba(255, 75, 43, 0.3);
            border-color: rgba(255, 75, 43, 0.3);
        }
        to { 
            box-shadow: 0 0 40px rgba(255, 75, 43, 0.8);
            border-color: rgba(255, 75, 43, 0.6);
        }
    }
    
    .status-live {
        display: inline-block;
        padding: 0.5rem 1rem;
        background: linear-gradient(45deg, #00ff88, #00cc6a);
        border-radius: 25px;
        color: black;
        font-weight: bold;
        animation: live-pulse 1.5s infinite;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
    }
    
    @keyframes live-pulse {
        0% { transform: scale(1); box-shadow: 0 0 20px rgba(0, 255, 136, 0.5); }
        50% { transform: scale(1.1); box-shadow: 0 0 30px rgba(0, 255, 136, 0.8); }
        100% { transform: scale(1); box-shadow: 0 0 20px rgba(0, 255, 136, 0.5); }
    }
    
    .ultimate-header {
        background: linear-gradient(90deg, #a855f7 0%, #ec4899 25%, #f97316 50%, #eab308 75%, #10b981 100%);
        background-size: 200% 200%;
        animation: rainbow-shift 4s ease infinite;
        padding: 2.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 20px 60px rgba(168, 85, 247, 0.4);
        border: 2px solid rgba(255, 255, 255, 0.2);
    }
    
    @keyframes rainbow-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 900;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        font-family: 'Orbitron', monospace;
    }
    
    .metric-medium {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        font-family: 'Orbitron', monospace;
    }
    
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
        margin: 0.5rem 0 0 0;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
    }
    
    .strategy-live-card {
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.2) 0%, rgba(236, 72, 153, 0.2) 100%);
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        border-left: 4px solid #a855f7;
        border: 1px solid rgba(168, 85, 247, 0.3);
        backdrop-filter: blur(10px);
        animation: subtle-glow 3s ease-in-out infinite;
    }
    
    @keyframes subtle-glow {
        0% { border-color: rgba(168, 85, 247, 0.3); }
        50% { border-color: rgba(168, 85, 247, 0.6); }
        100% { border-color: rgba(168, 85, 247, 0.3); }
    }
    
    .position-row {
        background: rgba(255,255,255,0.1);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #00d4aa;
        backdrop-filter: blur(5px);
    }
    
    .trade-profit {
        color: #00ff88;
        font-weight: 600;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }
    
    .trade-loss {
        color: #ff4b4b;
        font-weight: 600;
        text-shadow: 0 0 10px rgba(255, 75, 75, 0.5);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%);
        box-shadow: 0 0 20px rgba(168, 85, 247, 0.5);
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #a855f7, #ec4899);
        border-radius: 10px;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Make all text white by default */
    .stMarkdown, .stText, .stMetric {
        color: white !important;
    }
    
    .stMetric > div {
        color: white !important;
    }
    
    .stDataFrame {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        backdrop-filter: blur(10px);
    }
</style>
""", unsafe_allow_html=True)

# --- 🔧 CORE FUNCTIONS ---

def get_system_status():
    """Get system status"""
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
def load_active_strategies_only():
    """Load only active strategies with comprehensive data"""
    try:
        db_manager = DatabaseManager()
        
        # Load all data
        state = db_manager.load_full_portfolio_state()
        trade_log = db_manager.load_all_trades()
        open_positions_raw = db_manager.load_all_open_positions()
        
        # Filter only active strategies
        active_strategies = {}
        
        for strategy_name, strategy_data in state.items():
            # Check if strategy is truly active
            has_positions = strategy_name in open_positions_raw
            has_modified_capital = strategy_data.get('trading_capital', 100000) != 100000
            has_banked_profit = strategy_data.get('banked_profit', 0) != 0
            
            # Check recent activity (last 24 hours)
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
            
            # Only include if truly active
            if has_positions or has_modified_capital or has_banked_profit or has_recent_activity:
                active_strategies[strategy_name] = {
                    'data': strategy_data,
                    'positions': open_positions_raw.get(strategy_name, {}),
                    'trades': trade_log[trade_log['strategy_name'] == strategy_name] if not trade_log.empty else pd.DataFrame()
                }
        
        return active_strategies, None
        
    except Exception as e:
        return {}, str(e)

def parse_pnl(detail_str: str) -> float:
    """Extract PnL from details string"""
    if not isinstance(detail_str, str):
        return 0.0
    match = re.search(r"PnL:\s*(-?[\d,]+\.\d{2})", detail_str)
    return float(match.group(1).replace(",", "")) if match else 0.0

def calculate_professional_metrics(strategy_data):
    """Calculate comprehensive trading metrics"""
    trades_df = strategy_data['trades']
    positions = strategy_data['positions']
    portfolio = strategy_data['data']
    
    metrics = {
        'trading_capital': portfolio.get('trading_capital', 100000),
        'banked_profit': portfolio.get('banked_profit', 0),
        'open_positions_count': len(positions),
        'total_trades': 0,
        'win_rate': 0,
        'total_realized_pnl': 0,
        'unrealized_pnl': 0,
        'total_pnl': 0,
        'max_drawdown': 0,
        'sharpe_ratio': 0,
        'profit_factor': 0
    }
    
    # Calculate unrealized P&L from open positions
    total_unrealized = 0
    for symbol, details in positions.items():
        entry_price = details.get('entry_price', 0)
        current_price = details.get('current_price', entry_price)
        quantity = details.get('quantity', 0)
        action = details.get('action', '')
        
        if action == 'LONG':
            unrealized_pnl = (current_price - entry_price) * quantity
        else:
            unrealized_pnl = (entry_price - current_price) * quantity
        
        total_unrealized += unrealized_pnl
    
    metrics['unrealized_pnl'] = total_unrealized
    
    # Analyze completed trades
    if not trades_df.empty:
        exit_trades = trades_df[trades_df['action'].str.contains('EXIT', na=False)].copy()
        
        if not exit_trades.empty:
            exit_trades['PnL'] = exit_trades['details'].apply(parse_pnl)
            
            metrics['total_trades'] = len(exit_trades)
            metrics['total_realized_pnl'] = exit_trades['PnL'].sum()
            
            winning_trades = len(exit_trades[exit_trades['PnL'] > 0])
            metrics['win_rate'] = (winning_trades / len(exit_trades) * 100) if len(exit_trades) > 0 else 0
            
            # Calculate drawdown
            exit_trades['timestamp'] = pd.to_datetime(exit_trades['timestamp'])
            exit_trades = exit_trades.sort_values('timestamp')
            exit_trades['cumulative_pnl'] = exit_trades['PnL'].cumsum()
            
            if len(exit_trades) > 1:
                running_max = exit_trades['cumulative_pnl'].expanding().max()
                drawdown = (exit_trades['cumulative_pnl'] - running_max) / running_max * 100
                metrics['max_drawdown'] = abs(drawdown.min()) if not drawdown.empty else 0
            
            # Profit factor
            gross_profit = exit_trades[exit_trades['PnL'] > 0]['PnL'].sum()
            gross_loss = abs(exit_trades[exit_trades['PnL'] < 0]['PnL'].sum())
            metrics['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else 0
    
    metrics['total_pnl'] = metrics['total_realized_pnl'] + metrics['unrealized_pnl']
    
    return metrics

def create_capital_curve(strategy_name, trades_df):
    """Create capital curve chart"""
    if trades_df.empty:
        fig = go.Figure()
        fig.add_annotation(text=f"No trades data for {strategy_name}", 
                          xref="paper", yref="paper", x=0.5, y=0.5,
                          showarrow=False, font_size=16)
        fig.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        return fig
    
    exit_trades = trades_df[trades_df['action'].str.contains('EXIT', na=False)].copy()
    
    if exit_trades.empty:
        fig = go.Figure()
        fig.add_annotation(text=f"No completed trades for {strategy_name}", 
                          xref="paper", yref="paper", x=0.5, y=0.5,
                          showarrow=False, font_size=16)
        fig.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        return fig
    
    exit_trades['PnL'] = exit_trades['details'].apply(parse_pnl)
    exit_trades['timestamp'] = pd.to_datetime(exit_trades['timestamp'])
    exit_trades = exit_trades.sort_values('timestamp')
    exit_trades['cumulative_pnl'] = exit_trades['PnL'].cumsum()
    
    # Calculate capital curve
    initial_capital = 100000  # Base capital
    exit_trades['capital_curve'] = initial_capital + exit_trades['cumulative_pnl']
    
    fig = go.Figure()
    
    # Capital curve
    fig.add_trace(go.Scatter(
        x=exit_trades['timestamp'],
        y=exit_trades['capital_curve'],
        mode='lines+markers',
        name='Capital Curve',
        line=dict(color='#00d4aa', width=3),
        marker=dict(size=6, color='#00d4aa'),
        hovertemplate='<b>Capital: ₹%{y:,.0f}</b><br>Date: %{x}<extra></extra>'
    ))
    
    # Add baseline
    fig.add_hline(y=initial_capital, line_dash="dash", line_color="gray", 
                  annotation_text="Initial Capital")
    
    fig.update_layout(
        title=f'📈 {strategy_name} - Capital Curve',
        xaxis_title='Date',
        yaxis_title='Capital (₹)',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=400,
        showlegend=False
    )
    
    return fig

def create_pnl_distribution(strategy_name, trades_df):
    """Create P&L distribution chart"""
    if trades_df.empty:
        return go.Figure()
    
    exit_trades = trades_df[trades_df['action'].str.contains('EXIT', na=False)].copy()
    
    if exit_trades.empty:
        return go.Figure()
    
    exit_trades['PnL'] = exit_trades['details'].apply(parse_pnl)
    
    fig = go.Figure()
    
    # P&L histogram
    fig.add_trace(go.Histogram(
        x=exit_trades['PnL'],
        nbinsx=20,
        name='P&L Distribution',
        marker_color='rgba(0, 212, 170, 0.7)',
        hovertemplate='Range: ₹%{x}<br>Count: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'📊 {strategy_name} - P&L Distribution',
        xaxis_title='P&L (₹)',
        yaxis_title='Number of Trades',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=300
    )
    
    return fig

# --- 🚀 MAIN DASHBOARD ---

# Header
bot_running, market_open, current_time = get_system_status()

st.markdown(f"""
<div class="ultimate-header">
    <h1>⚡ ULTIMATE ACTIVE TRADING CONTROL CENTER ⚡</h1>
    <h3>🎯 Live Strategies • Real-time Performance • AI Analytics 🤖</h3>
    <div style="display: flex; justify-content: space-around; margin-top: 1.5rem;">
        <div>Bot: {'🟢 LIVE' if bot_running else '🔴 OFFLINE'}</div>
        <div>Market: {'🟢 OPEN' if market_open else '🔴 CLOSED'}</div>
        <div>Time: {current_time}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Load active strategies
with st.spinner("🔄 Loading active strategies..."):
    active_strategies, error = load_active_strategies_only()

if error:
    st.error(f"❌ Error: {error}")
    st.stop()

if not active_strategies:
    st.warning("⚠️ No active strategies found! All strategies appear to be inactive.")
    st.stop()

# --- OVERVIEW SECTION ---
st.markdown("## 📊 Active Strategies Overview")

# Calculate collective metrics
total_capital = 0
total_banked_profit = 0
total_unrealized_pnl = 0
total_positions = 0
total_trades = 0

strategy_metrics = {}
for strategy_name, strategy_data in active_strategies.items():
    metrics = calculate_professional_metrics(strategy_data)
    strategy_metrics[strategy_name] = metrics
    
    total_capital += metrics['trading_capital']
    total_banked_profit += metrics['banked_profit']
    total_unrealized_pnl += metrics['unrealized_pnl']
    total_positions += metrics['open_positions_count']
    total_trades += metrics['total_trades']

total_pnl = total_banked_profit + total_unrealized_pnl

# Overview cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    card_class = "profit-glow" if total_pnl > 0 else "loss-alert" if total_pnl < 0 else "neon-card"
    st.markdown(f"""
    <div class="{card_class}">
        <p class="metric-value">₹{total_pnl:,.0f}</p>
        <p class="metric-label">Total P&L</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="neon-card">
        <p class="metric-value">₹{total_capital:,.0f}</p>
        <p class="metric-label">Total Capital</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="neon-card">
        <p class="metric-value">{total_positions}</p>
        <p class="metric-label">Open Positions</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="neon-card">
        <p class="metric-value">{len(active_strategies)}</p>
        <p class="metric-label">Active Strategies</p>
    </div>
    """, unsafe_allow_html=True)

# Quick summary of each active strategy
st.markdown("### 🎯 Active Strategies Summary")

for strategy_name, metrics in strategy_metrics.items():
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div class="strategy-live-card">
            <strong style="color: white; font-family: Orbitron;">{strategy_name}</strong><br>
            <span class="status-live">🟢 LIVE</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric("Capital", f"₹{metrics['trading_capital']:,.0f}")
    
    with col3:
        st.metric("Realized P&L", f"₹{metrics['total_realized_pnl']:,.0f}")
    
    with col4:
        st.metric("Unrealized P&L", f"₹{metrics['unrealized_pnl']:,.0f}")
    
    with col5:
        st.metric("Win Rate", f"{metrics['win_rate']:.1f}%")
    
    with col6:
        st.metric("Positions", metrics['open_positions_count'])

# --- STRATEGY TABS ---
st.markdown("## 📋 Strategy Details")

tabs = st.tabs([f"📊 {name}" for name in active_strategies.keys()])

for i, (strategy_name, strategy_data) in enumerate(active_strategies.items()):
    with tabs[i]:
        metrics = strategy_metrics[strategy_name]
        
        # Strategy metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_strategy_pnl = metrics['total_pnl']
            card_class = "profit-glow" if total_strategy_pnl > 0 else "loss-alert" if total_strategy_pnl < 0 else "neon-card"
            st.markdown(f"""
            <div class="{card_class}">
                <p class="metric-medium">₹{total_strategy_pnl:,.0f}</p>
                <p class="metric-label">Total P&L</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="neon-card">
                <p class="metric-medium">₹{metrics['trading_capital']:,.0f}</p>
                <p class="metric-label">Capital</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="neon-card">
                <p class="metric-medium">{metrics['win_rate']:.1f}%</p>
                <p class="metric-label">Win Rate</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="neon-card">
                <p class="metric-medium">{metrics['max_drawdown']:.1f}%</p>
                <p class="metric-label">Max Drawdown</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="neon-card">
                <p class="metric-medium">{metrics['profit_factor']:.2f}</p>
                <p class="metric-label">Profit Factor</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Sub-tabs for detailed analysis
        subtab1, subtab2, subtab3, subtab4 = st.tabs(["📈 Capital Curve", "💼 Open Positions", "📊 P&L Analysis", "📋 Recent Trades"])
        
        with subtab1:
            fig_capital = create_capital_curve(strategy_name, strategy_data['trades'])
            st.plotly_chart(fig_capital, use_container_width=True, key=f"capital_{strategy_name}_{i}")
        
        with subtab2:
            positions = strategy_data['positions']
            if positions:
                st.markdown("#### 💼 Live Positions")
                
                position_data = []
                for symbol, details in positions.items():
                    entry_price = details.get('entry_price', 0)
                    current_price = details.get('current_price', entry_price)
                    quantity = details.get('quantity', 0)
                    action = details.get('action', '')
                    
                    if action == 'LONG':
                        unrealized_pnl = (current_price - entry_price) * quantity
                    else:
                        unrealized_pnl = (entry_price - current_price) * quantity
                    
                    pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                    
                    position_data.append({
                        "Symbol": symbol,
                        "Action": action,
                        "Quantity": quantity,
                        "Entry Price": f"₹{entry_price:.2f}",
                        "Current Price": f"₹{current_price:.2f}",
                        "Unrealized P&L": f"₹{unrealized_pnl:.2f}",
                        "% Change": f"{pnl_pct:.2f}%"
                    })
                
                df_positions = pd.DataFrame(position_data)
                st.dataframe(df_positions, use_container_width=True, hide_index=True)
                
                # Total unrealized P&L
                total_unrealized = sum(
                    (details.get('current_price', details.get('entry_price', 0)) - details.get('entry_price', 0)) * details.get('quantity', 0)
                    if details.get('action') == 'LONG' else
                    (details.get('entry_price', 0) - details.get('current_price', details.get('entry_price', 0))) * details.get('quantity', 0)
                    for details in positions.values()
                )
                
                pnl_color = "trade-profit" if total_unrealized >= 0 else "trade-loss"
                st.markdown(f'<p class="{pnl_color}"><strong>Total Unrealized P&L: ₹{total_unrealized:,.2f}</strong></p>', unsafe_allow_html=True)
            else:
                st.info("📋 No open positions")
        
        with subtab3:
            fig_dist = create_pnl_distribution(strategy_name, strategy_data['trades'])
            st.plotly_chart(fig_dist, use_container_width=True, key=f"pnl_dist_{strategy_name}_{i}")
            
            # Additional metrics
            if metrics['total_trades'] > 0:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Trades", metrics['total_trades'])
                
                with col2:
                    st.metric("Banked Profit", f"₹{metrics['banked_profit']:,.2f}")
                
                with col3:
                    avg_trade = metrics['total_realized_pnl'] / metrics['total_trades'] if metrics['total_trades'] > 0 else 0
                    st.metric("Avg Trade P&L", f"₹{avg_trade:.2f}")
        
        with subtab4:
            trades_df = strategy_data['trades']
            if not trades_df.empty:
                recent_trades = trades_df.tail(10).copy()
                recent_trades['timestamp'] = pd.to_datetime(recent_trades['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                
                # Add P&L for exit trades
                display_trades = recent_trades[['timestamp', 'symbol', 'action', 'price', 'quantity']].copy()
                
                # Add P&L column for EXIT trades
                pnl_values = []
                for _, trade in recent_trades.iterrows():
                    if 'EXIT' in str(trade['action']):
                        pnl = parse_pnl(str(trade['details']))
                        pnl_values.append(f"₹{pnl:,.2f}")
                    else:
                        pnl_values.append("-")
                
                display_trades['P&L'] = pnl_values
                
                st.dataframe(display_trades, use_container_width=True, hide_index=True)
            else:
                st.info("📋 No trades found")

# Auto-refresh controls
st.sidebar.markdown("## ⚙️ Controls")
auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh", value=True)
if auto_refresh:
    refresh_rate = st.sidebar.selectbox("Refresh Rate (seconds)", [3, 5, 10, 30], index=1)
    time.sleep(refresh_rate)
    st.rerun()

if st.sidebar.button("🔄 Manual Refresh"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(f"**🕐 Last Update:** {datetime.now().strftime('%H:%M:%S')}")
st.sidebar.markdown(f"**🎯 Active Strategies:** {len(active_strategies)}")
st.sidebar.markdown(f"**💼 Total Positions:** {total_positions}")
st.sidebar.markdown(f"**💰 Total P&L:** ₹{total_pnl:,.0f}")
