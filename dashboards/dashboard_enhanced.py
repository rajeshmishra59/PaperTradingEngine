# Enhanced Trading Dashboard - Vibrant & Powerful
# Features: Real-time charts, advanced analytics, modern UI, live monitoring

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

# --- 🎨 ADVANCED PAGE CONFIGURATION ---
st.set_page_config(
    page_title="🚀 AI Trading Control Center", 
    page_icon="📈", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🎯 CUSTOM CSS FOR VIBRANT UI ---
st.markdown("""
<style>
    /* Main dashboard styling */
    .main > div {
        padding-top: 1rem;
    }
    
    /* Gradient background for metrics cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Success/profit styling */
    .profit-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    
    /* Loss styling */
    .loss-card {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    
    /* Warning styling */
    .warning-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    
    /* Live indicator */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .live-indicator {
        animation: pulse 2s infinite;
        color: #ff4b2b;
        font-weight: bold;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Table styling */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# --- 🔧 ENHANCED HELPER FUNCTIONS ---

@st.cache_data(ttl=3)  # Ultra-fast refresh
def get_enhanced_data():
    """Get all dashboard data with enhanced metrics"""
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db_manager = st.session_state.db_manager
    
    state = db_manager.load_full_portfolio_state()
    trade_log = db_manager.load_all_trades()
    open_positions_raw = db_manager.load_all_open_positions()
    
    return state, trade_log, open_positions_raw

def get_system_status():
    """Get real-time system status"""
    try:
        # Check if main bot is running
        import subprocess
        result = subprocess.run(['pgrep', '-f', 'main_papertrader.py'], 
                              capture_output=True, text=True)
        bot_running = len(result.stdout.strip()) > 0
        
        # Check market status using timezone
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)
        market_open = (9, 15) <= (now_ist.hour, now_ist.minute) <= (15, 30)
        is_weekday = now_ist.weekday() < 5
        
        # Read latest log for heartbeat
        log_file = "logs/papertrading.log"
        last_heartbeat = None
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in reversed(lines[-20:]):
                    if "System alive" in line:
                        last_heartbeat = line.split(' - ')[0]
                        break
        
        return {
            'bot_running': bot_running,
            'market_open': market_open and is_weekday,
            'last_heartbeat': last_heartbeat,
            'current_time': now_ist.strftime('%H:%M:%S IST')
        }
    except:
        return {
            'bot_running': False,
            'market_open': False,
            'last_heartbeat': None,
            'current_time': 'N/A'
        }

def calculate_advanced_metrics(trade_log_df):
    """Calculate advanced trading metrics"""
    if trade_log_df.empty:
        return {}
    
    exit_trades = trade_log_df[trade_log_df['action'].str.contains('EXIT', na=False)].copy()
    if exit_trades.empty:
        return {}
    
    # Extract PnL
    exit_trades['PnL'] = exit_trades['details'].apply(parse_pnl)
    
    # Calculate metrics
    total_trades = len(exit_trades)
    winning_trades = len(exit_trades[exit_trades['PnL'] > 0])
    losing_trades = len(exit_trades[exit_trades['PnL'] <= 0])
    
    total_pnl = exit_trades['PnL'].sum()
    avg_win = exit_trades[exit_trades['PnL'] > 0]['PnL'].mean() if winning_trades > 0 else 0
    avg_loss = exit_trades[exit_trades['PnL'] <= 0]['PnL'].mean() if losing_trades > 0 else 0
    
    # Advanced metrics
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if avg_loss != 0 else 0
    
    # Consecutive wins/losses
    exit_trades_sorted = exit_trades.sort_values('timestamp')
    pnl_signs = (exit_trades_sorted['PnL'] > 0).astype(int)
    
    # Calculate streaks
    max_winning_streak = 0
    max_losing_streak = 0
    current_streak = 0
    last_sign = None
    
    for sign in pnl_signs:
        if sign == last_sign:
            current_streak += 1
        else:
            if last_sign == 1:  # Was winning
                max_winning_streak = max(max_winning_streak, current_streak)
            elif last_sign == 0:  # Was losing
                max_losing_streak = max(max_losing_streak, current_streak)
            current_streak = 1
            last_sign = sign
    
    # Handle final streak
    if last_sign == 1:
        max_winning_streak = max(max_winning_streak, current_streak)
    elif last_sign == 0:
        max_losing_streak = max(max_losing_streak, current_streak)
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'max_winning_streak': max_winning_streak,
        'max_losing_streak': max_losing_streak
    }

def parse_pnl(detail_str: str) -> float:
    """Extract PnL from details string"""
    if not isinstance(detail_str, str):
        return 0.0
    match = re.search(r"PnL:\s*(-?[\d,]+\.\d{2})", detail_str)
    return float(match.group(1).replace(",", "")) if match else 0.0

def create_pnl_chart(trade_log_df):
    """Create interactive PnL chart"""
    if trade_log_df.empty:
        return go.Figure()
    
    exit_trades = trade_log_df[trade_log_df['action'].str.contains('EXIT', na=False)].copy()
    if exit_trades.empty:
        return go.Figure()
    
    exit_trades['PnL'] = exit_trades['details'].apply(parse_pnl)
    exit_trades['timestamp'] = pd.to_datetime(exit_trades['timestamp'])
    exit_trades = exit_trades.sort_values('timestamp')
    exit_trades['Cumulative_PnL'] = exit_trades['PnL'].cumsum()
    
    fig = go.Figure()
    
    # Add cumulative PnL line
    fig.add_trace(go.Scatter(
        x=exit_trades['timestamp'],
        y=exit_trades['Cumulative_PnL'],
        mode='lines+markers',
        name='Cumulative P&L',
        line=dict(color='#00ff88', width=3),
        marker=dict(size=8, color='#00ff88'),
        hovertemplate='<b>%{y:.2f} ₹</b><br>%{x}<extra></extra>'
    ))
    
    # Add individual trade markers
    colors = ['#ff4b4b' if pnl < 0 else '#00ff88' for pnl in exit_trades['PnL']]
    fig.add_trace(go.Scatter(
        x=exit_trades['timestamp'],
        y=exit_trades['PnL'],
        mode='markers',
        name='Individual Trades',
        marker=dict(size=12, color=colors, opacity=0.7),
        hovertemplate='<b>%{y:.2f} ₹</b><br>%{x}<extra></extra>',
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='📈 P&L Performance Dashboard',
        xaxis_title='Time',
        yaxis_title='Cumulative P&L (₹)',
        yaxis2=dict(title='Individual Trade P&L (₹)', overlaying='y', side='right'),
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        showlegend=True,
        height=400
    )
    
    return fig

def create_strategy_performance_chart(state, trade_log_df):
    """Create strategy comparison chart"""
    if trade_log_df.empty:
        return go.Figure()
    
    exit_trades = trade_log_df[trade_log_df['action'].str.contains('EXIT', na=False)].copy()
    if exit_trades.empty:
        return go.Figure()
    
    exit_trades['PnL'] = exit_trades['details'].apply(parse_pnl)
    
    strategy_performance = exit_trades.groupby('strategy_name').agg({
        'PnL': ['sum', 'count', lambda x: (x > 0).sum()]
    }).round(2)
    
    strategy_performance.columns = ['Total_PnL', 'Total_Trades', 'Winning_Trades']
    strategy_performance['Win_Rate'] = (strategy_performance['Winning_Trades'] / 
                                       strategy_performance['Total_Trades'] * 100).round(2)
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('P&L by Strategy', 'Trade Count', 'Win Rate %', 'Strategy Capital'),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "pie"}]]
    )
    
    strategies = strategy_performance.index
    colors = px.colors.qualitative.Set3[:len(strategies)]
    
    # P&L by strategy
    fig.add_trace(go.Bar(
        x=strategies, y=strategy_performance['Total_PnL'],
        name='P&L', marker_color=colors,
        text=[f'₹{x:.2f}' for x in strategy_performance['Total_PnL']],
        textposition='auto'
    ), row=1, col=1)
    
    # Trade count
    fig.add_trace(go.Bar(
        x=strategies, y=strategy_performance['Total_Trades'],
        name='Trades', marker_color=colors,
        text=strategy_performance['Total_Trades'],
        textposition='auto'
    ), row=1, col=2)
    
    # Win rate
    fig.add_trace(go.Bar(
        x=strategies, y=strategy_performance['Win_Rate'],
        name='Win Rate', marker_color=colors,
        text=[f'{x:.1f}%' for x in strategy_performance['Win_Rate']],
        textposition='auto'
    ), row=2, col=1)
    
    # Strategy capital pie chart
    if state:
        capital_data = {k: v.get('trading_capital', 0) for k, v in state.items()}
        fig.add_trace(go.Pie(
            labels=list(capital_data.keys()),
            values=list(capital_data.values()),
            name='Capital Distribution'
        ), row=2, col=2)
    
    fig.update_layout(
        height=600,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    return fig

# --- 🚀 MAIN DASHBOARD ---

# Header with live status
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown("# 🚀 AI Trading Control Center")
    
with col2:
    system_status = get_system_status()
    if system_status['bot_running']:
        st.markdown('<div class="live-indicator">🟢 LIVE</div>', unsafe_allow_html=True)
    else:
        st.markdown('🔴 OFFLINE')
        
with col3:
    st.markdown(f"**{system_status['current_time']}**")

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh (5s)", value=True)
if auto_refresh:
    time.sleep(5)
    st.rerun()

# --- 📊 REAL-TIME METRICS DASHBOARD ---
st.markdown("## 📊 Live Performance Metrics")

# Get data
state, trade_log, open_positions_raw = get_enhanced_data()
metrics = calculate_advanced_metrics(trade_log)

# Top metrics row
if metrics:
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        pnl_color = "profit-card" if metrics['total_pnl'] >= 0 else "loss-card"
        st.markdown(f"""
        <div class="{pnl_color}">
            <h3>₹{metrics['total_pnl']:,.2f}</h3>
            <p>Total P&L</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{metrics['total_trades']}</h3>
            <p>Total Trades</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        win_color = "profit-card" if metrics['win_rate'] >= 50 else "warning-card"
        st.markdown(f"""
        <div class="{win_color}">
            <h3>{metrics['win_rate']:.1f}%</h3>
            <p>Win Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{metrics['profit_factor']:.2f}</h3>
            <p>Profit Factor</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        # Calculate total capital
        total_capital = sum(v.get('trading_capital', 0) for v in state.values()) if state else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>₹{total_capital:,.0f}</h3>
            <p>Total Capital</p>
        </div>
        """, unsafe_allow_html=True)

# --- 📈 INTERACTIVE CHARTS ---
st.markdown("## 📈 Interactive Analytics")

tab1, tab2, tab3 = st.tabs(["📊 P&L Performance", "🎯 Strategy Analysis", "📋 Live Positions"])

with tab1:
    st.plotly_chart(create_pnl_chart(trade_log), use_container_width=True)
    
    # Additional metrics
    if metrics:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Avg Win", f"₹{metrics['avg_win']:.2f}")
        with col2:
            st.metric("Avg Loss", f"₹{metrics['avg_loss']:.2f}")
        with col3:
            st.metric("Max Win Streak", metrics['max_winning_streak'])
        with col4:
            st.metric("Max Loss Streak", metrics['max_losing_streak'])

with tab2:
    st.plotly_chart(create_strategy_performance_chart(state, trade_log), use_container_width=True)

with tab3:
    # Live positions table
    if open_positions_raw:
        positions_list = []
        for strat, symbols in open_positions_raw.items():
            for symbol, details in symbols.items():
                positions_list.append({
                    "Strategy": strat,
                    "Symbol": symbol,
                    "Action": details.get('action'),
                    "Qty": details.get('quantity'),
                    "Entry Price": f"₹{details.get('entry_price', 0):.2f}",
                    "Current Price": f"₹{details.get('current_price', 0):.2f}",
                    "P&L": f"₹{((details.get('current_price', 0) - details.get('entry_price', 0)) * details.get('quantity', 0) * (1 if details.get('action') == 'LONG' else -1)):.2f}",
                    "Entry Time": details.get('entry_time')
                })
        
        if positions_list:
            df_positions = pd.DataFrame(positions_list)
            st.dataframe(df_positions, use_container_width=True, height=400)
        else:
            st.info("📈 No open positions")
    else:
        st.info("📈 No open positions")

# --- 🖥️ SYSTEM MONITORING ---
st.markdown("## 🖥️ System Status")

col1, col2 = st.columns([2, 1])

with col1:
    # System status indicators
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        bot_status = "🟢 RUNNING" if system_status['bot_running'] else "🔴 STOPPED"
        st.markdown(f"**Trading Bot:** {bot_status}")
    
    with status_col2:
        market_status = "🟢 OPEN" if system_status['market_open'] else "🔴 CLOSED"
        st.markdown(f"**Market:** {market_status}")
    
    with status_col3:
        heartbeat_status = "🟢 ACTIVE" if system_status['last_heartbeat'] else "🔴 NO SIGNAL"
        st.markdown(f"**Heartbeat:** {heartbeat_status}")

with col2:
    if st.button("🔄 Refresh Now", type="primary"):
        st.cache_data.clear()
        st.rerun()

# --- 📜 LIVE LOGS ---
st.markdown("## 📜 Live System Logs")
log_file = "logs/papertrading.log"
if os.path.exists(log_file):
    with open(log_file, 'r') as f:
        lines = f.readlines()
        recent_logs = "".join(lines[-30:])
    st.code(recent_logs, language='log')
else:
    st.warning("Log file not found")

# Footer
st.markdown("---")
st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')} | **Auto-refresh:** {'ON' if auto_refresh else 'OFF'}")
