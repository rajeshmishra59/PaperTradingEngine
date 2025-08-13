# Market Data Visualization Component
# Real-time market data charts and analysis

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database_manager import DatabaseManager

def create_market_heatmap(symbols_data):
    """Create a market heatmap showing price changes"""
    if not symbols_data:
        return go.Figure()
    
    # Sample data structure - adapt based on your data format
    symbols = list(symbols_data.keys())[:20]  # Limit to 20 for visibility
    
    # Calculate price changes (mock data - replace with actual logic)
    price_changes = np.random.uniform(-5, 5, len(symbols))
    volumes = np.random.uniform(1000, 10000, len(symbols))
    
    # Create grid layout
    rows = 4
    cols = 5
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=symbols,
        specs=[[{"type": "indicator"}] * cols for _ in range(rows)]
    )
    
    for i, (symbol, change, volume) in enumerate(zip(symbols, price_changes, volumes)):
        row = i // cols + 1
        col = i % cols + 1
        
        color = "green" if change >= 0 else "red"
        
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=change,
                delta={"reference": 0, "relative": True},
                title={"text": symbol},
                number={"suffix": "%", "font": {"color": color}},
                domain={'row': row-1, 'column': col-1}
            ),
            row=row, col=col
        )
    
    fig.update_layout(
        title="📊 Market Heatmap - Live Price Changes",
        height=600,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    return fig

def create_volume_analysis(trade_log_df):
    """Create volume analysis chart"""
    if trade_log_df.empty:
        return go.Figure()
    
    # Group by hour to show trading activity
    trade_log_df['timestamp'] = pd.to_datetime(trade_log_df['timestamp'])
    trade_log_df['hour'] = trade_log_df['timestamp'].dt.hour
    
    hourly_activity = trade_log_df.groupby('hour').size().reset_index(name='trade_count')
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=hourly_activity['hour'],
        y=hourly_activity['trade_count'],
        name='Trading Activity',
        marker_color='rgba(55, 83, 109, 0.8)',
        text=hourly_activity['trade_count'],
        textposition='auto'
    ))
    
    fig.update_layout(
        title='📊 Trading Activity by Hour',
        xaxis_title='Hour of Day',
        yaxis_title='Number of Trades',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=300
    )
    
    return fig

def create_symbol_performance_radar(trade_log_df):
    """Create radar chart for symbol performance"""
    if trade_log_df.empty:
        return go.Figure()
    
    # Get top 8 symbols by trade count
    symbol_stats = trade_log_df.groupby('symbol').agg({
        'timestamp': 'count',
        'details': lambda x: sum(1 for detail in x if 'PnL' in str(detail) and float(str(detail).split('PnL: ')[1].split(' ')[0]) > 0)
    }).rename(columns={'timestamp': 'total_trades', 'details': 'winning_trades'})
    
    symbol_stats['win_rate'] = (symbol_stats['winning_trades'] / symbol_stats['total_trades'] * 100).fillna(0)
    top_symbols = symbol_stats.nlargest(8, 'total_trades')
    
    if len(top_symbols) == 0:
        return go.Figure()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=top_symbols['win_rate'].values,
        theta=top_symbols.index.values,
        fill='toself',
        name='Win Rate %',
        line_color='rgba(0, 255, 136, 0.8)',
        fillcolor='rgba(0, 255, 136, 0.2)'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=(top_symbols['total_trades'] / top_symbols['total_trades'].max() * 100).values,
        theta=top_symbols.index.values,
        fill='toself',
        name='Trade Volume %',
        line_color='rgba(255, 75, 75, 0.8)',
        fillcolor='rgba(255, 75, 75, 0.2)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title="🎯 Symbol Performance Radar",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=400
    )
    
    return fig

def create_risk_metrics_gauge(metrics):
    """Create gauge charts for risk metrics"""
    if not metrics:
        return go.Figure()
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['Win Rate', 'Profit Factor', 'Drawdown Risk', 'Position Size'],
        specs=[[{"type": "indicator"}, {"type": "indicator"}],
               [{"type": "indicator"}, {"type": "indicator"}]]
    )
    
    # Win Rate Gauge
    win_rate = metrics.get('win_rate', 0)
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=win_rate,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Win Rate %"},
        delta={'reference': 50},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 30], 'color': "lightgray"},
                {'range': [30, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "green"}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90}}
    ), row=1, col=1)
    
    # Profit Factor Gauge
    profit_factor = min(metrics.get('profit_factor', 0), 5)  # Cap at 5 for display
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=profit_factor,
        title={'text': "Profit Factor"},
        gauge={
            'axis': {'range': [None, 5]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, 1], 'color': "red"},
                {'range': [1, 2], 'color': "yellow"},
                {'range': [2, 5], 'color': "green"}],
        }
    ), row=1, col=2)
    
    # Mock additional gauges
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=np.random.uniform(10, 90),
        title={'text': "Risk Level %"},
        gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "orange"}}
    ), row=2, col=1)
    
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=np.random.uniform(50, 100),
        title={'text': "Capital Utilization %"},
        gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "blue"}}
    ), row=2, col=2)
    
    fig.update_layout(
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    return fig
