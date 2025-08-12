#!/usr/bin/env python3
"""
DETAILED TRADE INVESTIGATION
Deep dive into all trades and open positions to understand the full picture
"""

import sqlite3
import pandas as pd
from datetime import datetime
import json

def detailed_investigation():
    """Comprehensive investigation of all trading activity"""
    conn = sqlite3.connect('trading_data.db')
    
    print("🕵️ DETAILED TRADE INVESTIGATION")
    print("=" * 60)
    
    # Load all trades with detailed analysis
    trades_df = pd.read_sql_query("""
        SELECT * FROM trades 
        ORDER BY timestamp, strategy_name, symbol
    """, conn)
    
    print(f"📊 Total Trade Records: {len(trades_df)}")
    
    # Analyze trade distribution
    print(f"\n📈 TRADE DISTRIBUTION:")
    action_counts = trades_df['action'].value_counts()
    for action, count in action_counts.items():
        print(f"   {action}: {count} trades")
    
    strategy_counts = trades_df['strategy_name'].value_counts()
    print(f"\n🎯 TRADES BY STRATEGY:")
    for strategy, count in strategy_counts.items():
        print(f"   {strategy}: {count} trades")
    
    symbol_counts = trades_df['symbol'].value_counts()
    print(f"\n📊 TOP TRADED SYMBOLS:")
    for symbol, count in symbol_counts.head(10).items():
        print(f"   {symbol}: {count} trades")
    
    # Analyze time distribution
    trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
    trades_df['date'] = trades_df['timestamp'].dt.date
    trades_df['hour'] = trades_df['timestamp'].dt.hour
    
    daily_trades = trades_df['date'].value_counts().sort_index()
    print(f"\n📅 DAILY TRADE ACTIVITY:")
    for date, count in daily_trades.items():
        print(f"   {date}: {count} trades")
    
    # Check for pattern in LONG vs SHORT
    print(f"\n🔍 DETAILED ACTION ANALYSIS:")
    for strategy in trades_df['strategy_name'].unique():
        strategy_trades = trades_df[trades_df['strategy_name'] == strategy]
        long_trades = len(strategy_trades[strategy_trades['action'] == 'LONG'])
        short_trades = len(strategy_trades[strategy_trades['action'] == 'SHORT'])
        
        print(f"   {strategy}:")
        print(f"     LONG entries: {long_trades}")
        print(f"     SHORT exits: {short_trades}")
        print(f"     Open positions: {long_trades - short_trades}")
    
    # Check open positions table
    positions_df = pd.read_sql_query("SELECT * FROM open_positions", conn)
    print(f"\n📋 OPEN POSITIONS TABLE:")
    print(positions_df[['strategy_name', 'symbol', 'position_details']])
    
    # Portfolio state analysis
    portfolio_df = pd.read_sql_query("SELECT * FROM portfolio_state", conn)
    print(f"\n💼 PORTFOLIO STATE:")
    for _, row in portfolio_df.iterrows():
        print(f"   {row['strategy_name']}:")
        print(f"     Initial Capital: ₹{row['initial_capital']:,.2f}")
        print(f"     Trading Capital: ₹{row['trading_capital']:,.2f}")
        print(f"     Banked Profit: ₹{row['banked_profit']:,.2f}")
        print(f"     Total Charges: ₹{row['total_charges']:,.2f}")
        
        # Calculate total value
        total_value = row['trading_capital'] + row['banked_profit']
        pnl = total_value - row['initial_capital']
        print(f"     Current Total Value: ₹{total_value:,.2f}")
        print(f"     Overall PnL: ₹{pnl:,.2f}")
    
    # Look for unmatched trades (positions still open)
    print(f"\n🔍 UNMATCHED TRADES ANALYSIS:")
    
    # Group by strategy and symbol to find unmatched
    unmatched_analysis = []
    
    for strategy in trades_df['strategy_name'].unique():
        strategy_trades = trades_df[trades_df['strategy_name'] == strategy]
        
        for symbol in strategy_trades['symbol'].unique():
            symbol_trades = strategy_trades[strategy_trades['symbol'] == symbol]
            
            long_count = len(symbol_trades[symbol_trades['action'] == 'LONG'])
            short_count = len(symbol_trades[symbol_trades['action'] == 'SHORT'])
            
            if long_count != short_count:
                unmatched_analysis.append({
                    'strategy': strategy,
                    'symbol': symbol,
                    'long_trades': long_count,
                    'short_trades': short_count,
                    'net_position': long_count - short_count
                })
    
    if unmatched_analysis:
        print("📊 SYMBOLS WITH OPEN POSITIONS:")
        for item in unmatched_analysis:
            print(f"   {item['symbol']} ({item['strategy']}):")
            print(f"     LONG: {item['long_trades']}, SHORT: {item['short_trades']}")
            print(f"     Net Position: {item['net_position']} (still open)")
    
    # Calculate potential PnL if we had current prices
    print(f"\n💡 ANALYSIS INSIGHTS:")
    print(f"   • Only {action_counts.get('SHORT', 0)} trades have been closed")
    print(f"   • {action_counts.get('LONG', 0)} positions were opened")
    print(f"   • {action_counts.get('LONG', 0) - action_counts.get('SHORT', 0)} positions still open")
    print(f"   • This explains why PnL analysis shows limited data")
    
    # Recent trading activity
    print(f"\n⏰ RECENT TRADING ACTIVITY (Last 10 trades):")
    recent_trades = trades_df.tail(10)[['timestamp', 'strategy_name', 'symbol', 'action', 'price', 'quantity']]
    for _, trade in recent_trades.iterrows():
        print(f"   {trade['timestamp'].strftime('%Y-%m-%d %H:%M')} | {trade['symbol']} | {trade['action']} | ₹{trade['price']} x {trade['quantity']}")
    
    conn.close()

if __name__ == "__main__":
    detailed_investigation()
