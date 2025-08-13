# 🚀 ULTIMATE AI Trading Dashboard - Maximum Power & Visual Appeal
# Features: Real-time monitoring, advanced analytics, market visualization, AI insights

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

# Import market visualization components
from market_viz import create_market_heatmap, create_volume_analysis, create_symbol_performance_radar, create_risk_metrics_gauge

# --- 🎨 ULTIMATE PAGE CONFIGURATION ---
st.set_page_config(
    page_title="🚀 Ultimate AI Trading Control Center", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🌈 ADVANCED VIBRANT STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    
    /* Futuristic main styling */
    .main > div {
        padding-top: 0.5rem;
        font-family: 'Orbitron', monospace;
    }
    
    /* Neon gradient cards */
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
        transition: transform 0.3s ease;
    }
    
    .neon-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(31, 38, 135, 0.5);
    }
    
    /* Profit glow effect */
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
    
    /* Loss alert effect */
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
    
    /* Live status indicators */
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
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        font-family: 'Orbitron', monospace;
    }
    
    /* Metric values */
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
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        font-weight: bold;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Remove streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Data tables */
    .dataframe {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Alert boxes */
    .alert-success {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    
    .alert-warning {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# --- 🔧 ENHANCED DATA FUNCTIONS ---

@st.cache_data(ttl=2)  # Ultra-fast 2-second cache
def get_ultimate_data():
    """Get comprehensive dashboard data"""
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db_manager = st.session_state.db_manager
    
    try:
        state = db_manager.load_full_portfolio_state()
        trade_log = db_manager.load_all_trades()
        open_positions_raw = db_manager.load_all_open_positions()
        
        return {
            'state': state,
            'trade_log': trade_log,
            'open_positions_raw': open_positions_raw,
            'status': 'success'
        }
    except Exception as e:
        return {
            'state': {},
            'trade_log': pd.DataFrame(),
            'open_positions_raw': {},
            'status': 'error',
            'error': str(e)
        }

def get_ai_insights(metrics, trade_log_df):
    """Generate AI-powered trading insights"""
    insights = []
    
    if not metrics:
        return ["🤖 Insufficient data for AI analysis"]
    
    # Performance insights
    win_rate = metrics.get('win_rate', 0)
    if win_rate > 70:
        insights.append("🎯 Excellent win rate! Your strategies are performing above market standards.")
    elif win_rate > 50:
        insights.append("📈 Good win rate. Consider optimizing entry signals for better performance.")
    else:
        insights.append("⚠️ Win rate needs improvement. Review and backtest your strategies.")
    
    # Profit factor insights
    profit_factor = metrics.get('profit_factor', 0)
    if profit_factor > 2:
        insights.append("💰 Outstanding profit factor! Your risk management is excellent.")
    elif profit_factor > 1.5:
        insights.append("✅ Solid profit factor. Your trading system is profitable.")
    elif profit_factor > 1:
        insights.append("📊 Marginally profitable. Consider tightening stop losses.")
    else:
        insights.append("🚨 Negative profit factor. Urgent strategy review required.")
    
    # Trading frequency insights
    total_trades = metrics.get('total_trades', 0)
    if total_trades > 50:
        insights.append("⚡ High trading frequency detected. Monitor for overtrading.")
    elif total_trades > 20:
        insights.append("📊 Good trading activity. Maintain consistency.")
    else:
        insights.append("🎯 Conservative trading approach. Consider increasing opportunities.")
    
    # Streak analysis
    max_win_streak = metrics.get('max_winning_streak', 0)
    max_loss_streak = metrics.get('max_losing_streak', 0)
    
    if max_loss_streak > 5:
        insights.append("⚠️ Long losing streak detected. Implement position sizing controls.")
    
    if max_win_streak > 10:
        insights.append("🔥 Impressive winning streak! Maintain momentum with disciplined risk management.")
    
    # Time-based insights
    if not trade_log_df.empty:
        trade_log_df['timestamp'] = pd.to_datetime(trade_log_df['timestamp'])
        recent_trades = trade_log_df[trade_log_df['timestamp'] > datetime.now() - timedelta(days=7)]
        
        if len(recent_trades) > len(trade_log_df) * 0.5:
            insights.append("📈 High recent activity. Monitor for market timing optimization.")
    
    return insights[:5]  # Limit to top 5 insights

def parse_pnl(detail_str: str) -> float:
    """Extract PnL from details string"""
    if not isinstance(detail_str, str):
        return 0.0
    match = re.search(r"PnL:\s*(-?[\d,]+\.\d{2})", detail_str)
    return float(match.group(1).replace(",", "")) if match else 0.0

def calculate_ultimate_metrics(trade_log_df):
    """Calculate comprehensive trading metrics"""
    if trade_log_df.empty:
        return {}
    
    exit_trades = trade_log_df[trade_log_df['action'].str.contains('EXIT', na=False)].copy()
    if exit_trades.empty:
        return {}
    
    exit_trades['PnL'] = exit_trades['details'].apply(parse_pnl)
    
    # Basic metrics
    total_trades = len(exit_trades)
    winning_trades = len(exit_trades[exit_trades['PnL'] > 0])
    losing_trades = len(exit_trades[exit_trades['PnL'] <= 0])
    
    total_pnl = exit_trades['PnL'].sum()
    avg_win = exit_trades[exit_trades['PnL'] > 0]['PnL'].mean() if winning_trades > 0 else 0
    avg_loss = exit_trades[exit_trades['PnL'] <= 0]['PnL'].mean() if losing_trades > 0 else 0
    
    # Advanced metrics
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if avg_loss != 0 else 0
    
    # Risk metrics
    returns = exit_trades['PnL'].values
    max_drawdown = 0
    peak = 0
    cumulative_returns = np.cumsum(returns)
    
    for value in cumulative_returns:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak if peak != 0 else 0
        max_drawdown = max(max_drawdown, drawdown)
    
    # Sharpe ratio (simplified)
    sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) != 0 else 0
    
    # Consecutive streaks
    exit_trades_sorted = exit_trades.sort_values('timestamp')
    pnl_signs = (exit_trades_sorted['PnL'] > 0).astype(int)
    
    max_winning_streak = 0
    max_losing_streak = 0
    current_streak = 0
    last_sign = None
    
    for sign in pnl_signs:
        if sign == last_sign:
            current_streak += 1
        else:
            if last_sign == 1:
                max_winning_streak = max(max_winning_streak, current_streak)
            elif last_sign == 0:
                max_losing_streak = max(max_losing_streak, current_streak)
            current_streak = 1
            last_sign = sign
    
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
        'max_drawdown': max_drawdown * 100,
        'sharpe_ratio': sharpe_ratio,
        'max_winning_streak': max_winning_streak,
        'max_losing_streak': max_losing_streak
    }

def get_system_vitals():
    """Get comprehensive system status"""
    try:
        import subprocess
        import psutil
        
        # Bot status - check for any main_papertrader process
        result = subprocess.run(['pgrep', '-f', 'main_papertrader'], 
                              capture_output=True, text=True)
        bot_running = len(result.stdout.strip()) > 0
        
        # Also check ps aux as backup
        if not bot_running:
            ps_result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            bot_running = 'main_papertrader' in ps_result.stdout
        
        # Market status
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)
        market_open = (9, 15) <= (now_ist.hour, now_ist.minute) <= (15, 30)
        is_weekday = now_ist.weekday() < 5
        
        # System resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        # Last heartbeat
        log_file = "logs/papertrading.log"
        last_heartbeat = None
        heartbeat_age = None
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in reversed(lines[-50:]):
                    if "System alive" in line:
                        try:
                            timestamp_str = line.split(' - ')[0]
                            heartbeat_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                            heartbeat_age = (datetime.now() - heartbeat_time).total_seconds()
                            last_heartbeat = timestamp_str
                        except:
                            pass
                        break
        
        return {
            'bot_running': bot_running,
            'market_open': market_open and is_weekday,
            'last_heartbeat': last_heartbeat,
            'heartbeat_age': heartbeat_age,
            'current_time': now_ist.strftime('%H:%M:%S IST'),
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'disk_percent': disk_percent,
            'system_health': 'excellent' if cpu_percent < 50 and memory_percent < 70 else 'good' if cpu_percent < 80 and memory_percent < 85 else 'poor'
        }
    except Exception as e:
        return {
            'bot_running': False,
            'market_open': False,
            'last_heartbeat': None,
            'heartbeat_age': None,
            'current_time': 'N/A',
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_percent': 0,
            'system_health': 'unknown',
            'error': str(e)
        }

def create_ultimate_pnl_chart(trade_log_df):
    """Create the ultimate P&L visualization"""
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
    
    # Cumulative P&L with gradient fill
    fig.add_trace(go.Scatter(
        x=exit_trades['timestamp'],
        y=exit_trades['Cumulative_PnL'],
        mode='lines+markers',
        name='Cumulative P&L',
        line=dict(color='#00ff88', width=4),
        marker=dict(size=8, color='#00ff88', line=dict(width=2, color='white')),
        fill='tonexty',
        fillcolor='rgba(0, 255, 136, 0.2)',
        hovertemplate='<b>₹%{y:,.2f}</b><br>%{x}<extra></extra>'
    ), row=1, col=1)
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)
    
    # Individual trades with color coding
    colors = ['#ff4b4b' if pnl < 0 else '#00ff88' for pnl in exit_trades['PnL']]
    
    fig.add_trace(go.Bar(
        x=exit_trades['timestamp'],
        y=exit_trades['PnL'],
        name='Trade P&L',
        marker_color=colors,
        opacity=0.8,
        hovertemplate='<b>₹%{y:,.2f}</b><br>%{x}<extra></extra>'
    ), row=2, col=1)
    
    # Add moving average
    if len(exit_trades) > 5:
        exit_trades['MA_PnL'] = exit_trades['Cumulative_PnL'].rolling(window=min(5, len(exit_trades))).mean()
        fig.add_trace(go.Scatter(
            x=exit_trades['timestamp'],
            y=exit_trades['MA_PnL'],
            mode='lines',
            name='Moving Average',
            line=dict(color='yellow', width=2, dash='dot'),
            opacity=0.7
        ), row=1, col=1)
    
    fig.update_layout(
        title='🚀 Ultimate P&L Analytics Dashboard',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='Orbitron'),
        showlegend=True,
        height=700,
        hovermode='x unified'
    )
    
    return fig

# --- 🚀 ULTIMATE DASHBOARD MAIN INTERFACE ---

# Header with system vitals
vitals = get_system_vitals()

st.markdown(f"""
<div class="main-header">
    <h1>⚡ ULTIMATE AI TRADING CONTROL CENTER ⚡</h1>
    <h3>Advanced Analytics • Real-time Monitoring • AI Insights</h3>
</div>
""", unsafe_allow_html=True)

# System status bar
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    status_class = "status-live" if vitals['bot_running'] else "status-offline"
    status_text = "🟢 LIVE" if vitals['bot_running'] else "🔴 OFFLINE"
    st.markdown(f'<div class="{status_class}">{status_text}</div>', unsafe_allow_html=True)

with col2:
    market_status = "🟢 OPEN" if vitals['market_open'] else "🔴 CLOSED"
    st.markdown(f"**Market:** {market_status}")

with col3:
    st.markdown(f"**Time:** {vitals['current_time']}")

with col4:
    health_emoji = "💚" if vitals['system_health'] == 'excellent' else "💛" if vitals['system_health'] == 'good' else "❤️"
    st.markdown(f"**Health:** {health_emoji} {vitals['system_health'].upper()}")

with col5:
    if vitals['heartbeat_age'] and vitals['heartbeat_age'] < 120:
        st.markdown("**Status:** 💓 ACTIVE")
    else:
        st.markdown("**Status:** ⚠️ STALE")

# Auto-refresh controls
st.sidebar.markdown("## ⚙️ Control Panel")
auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh", value=True)
refresh_interval = st.sidebar.selectbox("Refresh Rate", [2, 5, 10, 30], index=1)

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

# Get dashboard data
data = get_ultimate_data()

if data['status'] == 'error':
    st.error(f"❌ Database Error: {data['error']}")
    st.stop()

state = data['state']
trade_log = data['trade_log']
open_positions_raw = data['open_positions_raw']

# Calculate metrics
metrics = calculate_ultimate_metrics(trade_log)
ai_insights = get_ai_insights(metrics, trade_log)

# --- 📊 ULTIMATE METRICS DASHBOARD ---
st.markdown("## 🎯 Live Performance Metrics")

if metrics:
    # Top row - Primary metrics
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
        pf = metrics['profit_factor']
        card_class = "profit-glow" if pf >= 2 else "neon-card" if pf >= 1.5 else "loss-alert"
        st.markdown(f"""
        <div class="{card_class}">
            <p class="metric-value">{pf:.2f}</p>
            <p class="metric-label">Profit Factor</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        sharpe = metrics['sharpe_ratio']
        card_class = "profit-glow" if sharpe >= 1 else "neon-card" if sharpe >= 0.5 else "loss-alert"
        st.markdown(f"""
        <div class="{card_class}">
            <p class="metric-value">{sharpe:.2f}</p>
            <p class="metric-label">Sharpe Ratio</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Second row - Advanced metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("💰 Avg Win", f"₹{metrics['avg_win']:,.2f}")
    with col2:
        st.metric("💸 Avg Loss", f"₹{metrics['avg_loss']:,.2f}")
    with col3:
        st.metric("📈 Max Win Streak", metrics['max_winning_streak'])
    with col4:
        st.metric("📉 Max Loss Streak", metrics['max_losing_streak'])
    with col5:
        st.metric("⚠️ Max Drawdown", f"{metrics['max_drawdown']:.1f}%")

# --- 🤖 AI INSIGHTS PANEL ---
st.markdown("## 🤖 AI Trading Insights")
insight_cols = st.columns(len(ai_insights) if ai_insights else 1)

for i, insight in enumerate(ai_insights):
    with insight_cols[i % len(insight_cols)]:
        st.markdown(f"""
        <div class="alert-success">
            {insight}
        </div>
        """, unsafe_allow_html=True)

# --- 📈 ULTIMATE ANALYTICS SECTION ---
st.markdown("## 📈 Advanced Analytics Suite")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 P&L Analytics", 
    "🎯 Strategy Performance", 
    "📋 Live Positions", 
    "🌡️ Risk Metrics",
    "🏛️ Market Overview"
])

with tab1:
    st.plotly_chart(create_ultimate_pnl_chart(trade_log), use_container_width=True)

with tab2:
    if not trade_log.empty:
        st.plotly_chart(create_symbol_performance_radar(trade_log), use_container_width=True)
        st.plotly_chart(create_volume_analysis(trade_log), use_container_width=True)
    else:
        st.info("📈 No strategy data available yet")

with tab3:
    # Enhanced live positions display
    if open_positions_raw:
        positions_list = []
        total_unrealized = 0
        
        for strat, symbols in open_positions_raw.items():
            for symbol, details in symbols.items():
                entry_price = details.get('entry_price', 0)
                current_price = details.get('current_price', entry_price)
                quantity = details.get('quantity', 0)
                action = details.get('action', '')
                
                # Calculate unrealized P&L
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
                    "% Change": f"{((current_price - entry_price) / entry_price * 100):.2f}%",
                    "Entry Time": details.get('entry_time', '')
                })
        
        if positions_list:
            # Show total unrealized P&L
            pnl_color = "profit-glow" if total_unrealized >= 0 else "loss-alert"
            st.markdown(f"""
            <div class="{pnl_color}">
                <h3>Total Unrealized P&L: ₹{total_unrealized:,.2f}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Display positions table
            df_positions = pd.DataFrame(positions_list)
            st.dataframe(df_positions, use_container_width=True, height=400)
        else:
            st.info("📈 No open positions")
    else:
        st.info("📈 No open positions")

with tab4:
    if metrics:
        st.plotly_chart(create_risk_metrics_gauge(metrics), use_container_width=True)
    else:
        st.info("📊 Insufficient data for risk analysis")

with tab5:
    # Market overview with system data
    if state:
        st.plotly_chart(create_market_heatmap(state), use_container_width=True)
    else:
        st.info("🏛️ Market data not available")

# --- 🖥️ SYSTEM MONITORING SECTION ---
st.markdown("## 🖥️ System Vital Signs")

col1, col2 = st.columns([3, 1])

with col1:
    # System resource gauges
    resource_fig = go.Figure()
    
    resource_fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=vitals['cpu_percent'],
        title={'text': "CPU Usage %"},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "blue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgreen"},
                {'range': [50, 80], 'color': "yellow"},
                {'range': [80, 100], 'color': "red"}
            ]
        },
        domain={'row': 0, 'column': 0}
    ))
    
    resource_fig.add_trace(go.Indicator(
        mode="gauge+number", 
        value=vitals['memory_percent'],
        title={'text': "Memory Usage %"},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, 70], 'color': "lightgreen"},
                {'range': [70, 85], 'color': "yellow"},
                {'range': [85, 100], 'color': "red"}
            ]
        },
        domain={'row': 0, 'column': 1}
    ))
    
    resource_fig.update_layout(
        grid={'rows': 1, 'columns': 2, 'pattern': "independent"},
        height=300,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    st.plotly_chart(resource_fig, use_container_width=True)

with col2:
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🔄 Force Refresh", type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    if st.button("📊 Export Data", type="secondary"):
        if not trade_log.empty:
            csv = trade_log.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV",
                data=csv,
                file_name=f"trading_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    if st.button("🚨 Emergency Stop", type="secondary"):
        st.warning("⚠️ Emergency stop would be triggered in live system")

# --- 📜 ENHANCED LIVE LOGS ---
st.markdown("## 📜 Live System Intelligence")

log_tab1, log_tab2 = st.tabs(["📋 Recent Activity", "⚠️ System Alerts"])

with log_tab1:
    log_file = "logs/papertrading.log"
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_logs = "".join(lines[-50:])
        
        # Color-code log levels
        if recent_logs:
            st.code(recent_logs, language='log')
        else:
            st.info("No recent logs available")
    else:
        st.warning("📋 Log file not found")

with log_tab2:
    # Show any error patterns or warnings
    alerts = []
    if vitals['heartbeat_age'] and vitals['heartbeat_age'] > 300:
        alerts.append("⚠️ No heartbeat for > 5 minutes")
    if vitals['cpu_percent'] > 80:
        alerts.append("🔥 High CPU usage detected")
    if vitals['memory_percent'] > 85:
        alerts.append("💾 High memory usage detected")
    
    if alerts:
        for alert in alerts:
            st.markdown(f"""
            <div class="alert-warning">
                {alert}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="alert-success">
            ✅ All systems operating normally
        </div>
        """, unsafe_allow_html=True)

# Footer with live stats
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"**🕐 Last Updated:** {datetime.now().strftime('%H:%M:%S IST')}")
with col2:
    st.markdown(f"**🔄 Auto-refresh:** {'ON' if auto_refresh else 'OFF'} ({refresh_interval}s)")
with col3:
    if vitals['last_heartbeat']:
        st.markdown(f"**💓 Last Heartbeat:** {vitals['last_heartbeat']}")
    else:
        st.markdown("**💓 Last Heartbeat:** No signal")

# Add some JavaScript for enhanced interactivity
st.markdown("""
<script>
// Add some dynamic effects
document.addEventListener('DOMContentLoaded', function() {
    // Add floating animation to metric cards
    const cards = document.querySelectorAll('.neon-card, .profit-glow, .loss-alert');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });
});
</script>
""", unsafe_allow_html=True)
