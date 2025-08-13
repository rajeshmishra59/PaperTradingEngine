# 🚀 FOCUSED Trading Dashboard - Only Active Strategies
# Shows only strategies that are currently running with positions or recent activity

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
    page_title="🎯 Active Trading Strategies", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 🌈 CLEAN STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    .main > div {
        padding-top: 0.5rem;
        font-family: 'Inter', sans-serif;
    }
    
    .active-strategy {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(31, 38, 135, 0.3);
        color: white;
        margin-bottom: 1rem;
        border-left: 5px solid #00ff88;
    }
    
    .profit-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    
    .loss-card {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    
    .neutral-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    
    .status-live {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        background: #00ff88;
        border-radius: 15px;
        color: black;
        font-weight: 600;
        font-size: 0.8rem;
    }
    
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        text-align: center;
        color: white;
    }
    
    .metric-big {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
    }
    
    .metric-small {
        font-size: 0.9rem;
        opacity: 0.8;
        margin: 0;
    }
    
    .position-row {
        background: rgba(255,255,255,0.1);
        padding: 0.5rem;
        border-radius: 8px;
        margin: 0.3rem 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 🔧 DATA FUNCTIONS ---

def get_system_status():
    """Get basic system status"""
    try:
        # Bot status
        result = subprocess.run(['pgrep', '-f', 'main_papertrader'], 
                              capture_output=True, text=True)
        bot_running = len(result.stdout.strip()) > 0
        
        # Market status
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
        
        # Get all data
        state = db_manager.load_full_portfolio_state()
        trade_log = db_manager.load_all_trades()
        open_positions_raw = db_manager.load_all_open_positions()
        
        # Find active strategies
        active_strategies = set()
        
        # 1. Strategies with open positions
        if open_positions_raw:
            active_strategies.update(open_positions_raw.keys())
        
        # 2. Strategies with recent activity (last 24 hours)
        if not trade_log.empty:
            trade_log['timestamp'] = pd.to_datetime(trade_log['timestamp'])
            # Make both timestamps timezone-aware for comparison
            ist = pytz.timezone('Asia/Kolkata')
            recent_cutoff = datetime.now(ist) - timedelta(hours=24)
            # Convert cutoff to UTC to match database timestamps
            recent_cutoff = recent_cutoff.astimezone(pytz.UTC).replace(tzinfo=None)
            
            # Make trade timestamps timezone-naive for comparison
            trade_log['timestamp_naive'] = trade_log['timestamp'].dt.tz_localize(None)
            recent_trades = trade_log[trade_log['timestamp_naive'] > recent_cutoff]
            if not recent_trades.empty:
                active_strategies.update(recent_trades['strategy_name'].unique())
        
        # 3. Strategies with actual trading capital changes (not initial 100k)
        if state:
            for strategy, data in state.items():
                trading_capital = data.get('trading_capital', 100000)
                banked_profit = data.get('banked_profit', 0)
                if trading_capital != 100000 or banked_profit != 0:
                    active_strategies.add(strategy)
        
        # Filter data for active strategies only
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
    """Create P&L chart for specific strategy"""
    strategy_trades = trade_log_df[trade_log_df['strategy_name'] == strategy_name]
    exit_trades = strategy_trades[strategy_trades['action'].str.contains('EXIT', na=False)].copy()
    
    if exit_trades.empty:
        fig = go.Figure()
        fig.add_annotation(text=f"No completed trades for {strategy_name}", 
                          xref="paper", yref="paper", x=0.5, y=0.5, 
                          showarrow=False, font_size=16)
        fig.update_layout(height=300, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        return fig
    
    exit_trades['PnL'] = exit_trades['details'].apply(parse_pnl)
    exit_trades['timestamp'] = pd.to_datetime(exit_trades['timestamp'])
    exit_trades = exit_trades.sort_values('timestamp')
    exit_trades['Cumulative_PnL'] = exit_trades['PnL'].cumsum()
    
    fig = go.Figure()
    
    # Cumulative P&L line
    fig.add_trace(go.Scatter(
        x=exit_trades['timestamp'],
        y=exit_trades['Cumulative_PnL'],
        mode='lines+markers',
        name='Cumulative P&L',
        line=dict(color='#00ff88' if exit_trades['Cumulative_PnL'].iloc[-1] >= 0 else '#ff4b4b', width=3),
        marker=dict(size=6),
        hovertemplate='<b>₹%{y:,.2f}</b><br>%{x}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'{strategy_name} - P&L Performance',
        height=300,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        showlegend=False
    )
    
    return fig

# --- 🚀 MAIN DASHBOARD ---

# Header with system status
bot_running, market_open, current_time = get_system_status()

st.markdown(f"""
<div class="main-header">
    <h2>🎯 Active Trading Strategies Monitor</h2>
    <div style="display: flex; justify-content: space-around; margin-top: 1rem;">
        <div>Bot: {'🟢 LIVE' if bot_running else '🔴 OFF'}</div>
        <div>Market: {'🟢 OPEN' if market_open else '🔴 CLOSED'}</div>
        <div>Time: {current_time}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Load active strategies data
with st.spinner("🔍 Loading active strategies..."):
    state, trade_log, open_positions, active_strategies, error = load_active_strategies()

if error:
    st.error(f"❌ Error: {error}")
    st.stop()

if not active_strategies:
    st.warning("⚠️ No active strategies found. All strategies appear to be inactive.")
    st.info("💡 Strategies are considered active if they have:")
    st.write("• Open positions")
    st.write("• Recent trading activity (last 24 hours)")  
    st.write("• Modified capital from initial allocation")
    st.stop()

st.success(f"✅ Found {len(active_strategies)} active strategies")

# Display each active strategy
for strategy_name in active_strategies:
    st.markdown(f"## 🎯 {strategy_name}")
    
    # Get strategy metrics
    metrics = calculate_strategy_metrics(trade_log, strategy_name)
    strategy_state = state.get(strategy_name, {})
    strategy_positions = open_positions.get(strategy_name, {})
    
    # Strategy overview cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        capital = strategy_state.get('trading_capital', 0)
        card_class = "profit-card" if capital > 100000 else "loss-card" if capital < 100000 else "neutral-card"
        st.markdown(f"""
        <div class="{card_class}">
            <p class="metric-big">₹{capital:,.0f}</p>
            <p class="metric-small">Trading Capital</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        profit = strategy_state.get('banked_profit', 0)
        card_class = "profit-card" if profit > 0 else "loss-card" if profit < 0 else "neutral-card"
        st.markdown(f"""
        <div class="{card_class}">
            <p class="metric-big">₹{profit:,.2f}</p>
            <p class="metric-small">Banked Profit</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_pnl = metrics.get('total_pnl', 0)
        card_class = "profit-card" if total_pnl > 0 else "loss-card" if total_pnl < 0 else "neutral-card"
        st.markdown(f"""
        <div class="{card_class}">
            <p class="metric-big">₹{total_pnl:,.0f}</p>
            <p class="metric-small">Total P&L</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        win_rate = metrics.get('win_rate', 0)
        card_class = "profit-card" if win_rate >= 60 else "loss-card" if win_rate < 40 else "neutral-card"
        st.markdown(f"""
        <div class="{card_class}">
            <p class="metric-big">{win_rate:.1f}%</p>
            <p class="metric-small">Win Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Strategy tabs
    tab1, tab2, tab3 = st.tabs(["📊 Performance Chart", "📋 Open Positions", "📈 Recent Trades"])
    
    with tab1:
        if metrics.get('total_trades', 0) > 0:
            fig = create_strategy_pnl_chart(trade_log, strategy_name)
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
                # Show total unrealized P&L
                total_color = "profit-card" if total_unrealized >= 0 else "loss-card"
                st.markdown(f"""
                <div class="{total_color}">
                    <h4>Total Unrealized P&L: ₹{total_unrealized:,.2f}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Show positions table
                df_positions = pd.DataFrame(position_data)
                st.dataframe(df_positions, use_container_width=True, hide_index=True)
            else:
                st.info("📋 No position details available")
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

# Summary footer
st.markdown("### 📊 Active Strategies Summary")
total_active = len(active_strategies)
total_positions = sum(len(positions) for positions in open_positions.values())
total_capital = sum(data.get('trading_capital', 0) for data in state.values())

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("🎯 Active Strategies", total_active)
with col2:
    st.metric("📋 Total Positions", total_positions)
with col3:
    st.metric("💰 Total Capital", f"₹{total_capital:,.0f}")

# Auto refresh option
if st.sidebar.checkbox("🔄 Auto Refresh (5s)", value=False):
    time.sleep(5)
    st.rerun()

st.sidebar.markdown(f"**Last Updated:** {datetime.now().strftime('%H:%M:%S')}")
st.sidebar.markdown(f"**Active:** {', '.join(active_strategies)}")
