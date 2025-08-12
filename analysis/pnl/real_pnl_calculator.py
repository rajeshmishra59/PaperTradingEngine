#!/usr/bin/env python3
"""
REAL PnL CALCULATOR 
Calculate the actual PnL including open positions using current portfolio state
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime

def calculate_real_pnl():
    """Calculate real PnL including unrealized gains/losses"""
    
    print("💰 REAL PnL ANALYSIS - INCLUDING OPEN POSITIONS")
    print("=" * 60)
    
    conn = sqlite3.connect('trading_data.db')
    
    # Get portfolio state
    portfolio_df = pd.read_sql_query("SELECT * FROM portfolio_state", conn)
    active_strategy = 'SankhyaEkStrategy'  # Only this one has trades
    
    strategy_data = portfolio_df[portfolio_df['strategy_name'] == active_strategy].iloc[0]
    
    initial_capital = strategy_data['initial_capital']
    current_capital = strategy_data['trading_capital']
    banked_profit = strategy_data['banked_profit']
    total_charges = strategy_data['total_charges']
    
    print(f"📊 PORTFOLIO ANALYSIS FOR {active_strategy}:")
    print(f"   Initial Capital: ₹{initial_capital:,.2f}")
    print(f"   Current Trading Capital: ₹{current_capital:,.2f}")
    print(f"   Banked Profit: ₹{banked_profit:,.2f}")
    print(f"   Total Charges Paid: ₹{total_charges:,.2f}")
    
    # Calculate net capital usage
    capital_used = initial_capital - current_capital
    print(f"   Capital Used in Trades: ₹{capital_used:,.2f}")
    
    # Calculate realized PnL from closed trades
    trades_df = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp", conn)
    trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
    
    print(f"\n🔍 TRADE ANALYSIS:")
    print(f"   Total Trade Records: {len(trades_df)}")
    
    action_counts = trades_df['action'].value_counts()
    for action, count in action_counts.items():
        print(f"   {action}: {count}")
    
    # Calculate realized PnL from EXIT trades
    exit_trades = trades_df[trades_df['action'].str.contains('EXIT', na=False)]
    final_exit_trades = trades_df[trades_df['action'].str.contains('FINAL_EXIT', na=False)]
    
    print(f"\n📈 REALIZED TRADES:")
    print(f"   Normal Exits: {len(exit_trades)}")
    print(f"   Final Exits (Stop Loss): {len(final_exit_trades)}")
    
    # Estimate realized PnL from charges and capital movement
    # If we spent charges but capital reduced more than trades, there are losses
    net_effect = initial_capital - current_capital - banked_profit
    
    print(f"\n💸 FINANCIAL IMPACT:")
    print(f"   Net Capital Lost: ₹{net_effect:,.2f}")
    print(f"   Charges Paid: ₹{total_charges:,.2f}")
    print(f"   Trading Loss (approx): ₹{net_effect - total_charges:,.2f}")
    
    # Current position analysis
    positions_df = pd.read_sql_query("SELECT * FROM open_positions", conn)
    
    print(f"\n📋 CURRENT OPEN POSITIONS: {len(positions_df)}")
    
    total_position_value = 0
    for _, pos in positions_df.iterrows():
        details = json.loads(pos['position_details'])
        symbol = pos['symbol']
        action = details['action']
        entry_price = details['entry_price']
        quantity = details['quantity']
        position_value = entry_price * quantity
        total_position_value += position_value
        
        print(f"   {symbol}: {action} @ ₹{entry_price} x {quantity} = ₹{position_value:,.2f}")
    
    print(f"\n💼 POSITION SUMMARY:")
    print(f"   Total Position Value: ₹{total_position_value:,.2f}")
    print(f"   Available Cash: ₹{current_capital:,.2f}")
    print(f"   Total Account Value: ₹{current_capital + total_position_value:,.2f}")
    
    # Calculate unrealized PnL (approximate)
    unrealized_pnl = (current_capital + total_position_value) - initial_capital
    
    print(f"\n🎯 PERFORMANCE SUMMARY:")
    print(f"   Starting Capital: ₹{initial_capital:,.2f}")
    print(f"   Current Total Value: ₹{current_capital + total_position_value:,.2f}")
    print(f"   Unrealized PnL: ₹{unrealized_pnl:,.2f}")
    print(f"   Performance: {(unrealized_pnl/initial_capital)*100:.2f}%")
    
    if unrealized_pnl < 0:
        print(f"   🚨 LOSS: ₹{abs(unrealized_pnl):,.2f}")
    else:
        print(f"   ✅ PROFIT: ₹{unrealized_pnl:,.2f}")
    
    # Analyze loss patterns
    print(f"\n🔍 LOSS PATTERN ANALYSIS:")
    
    # Count different types of exits
    loss_exits = trades_df[trades_df['action'].str.contains('LOSS', na=False)]
    print(f"   Stop Loss Exits: {len(loss_exits)}")
    
    if len(loss_exits) > 0:
        print(f"   Stop Loss Symbols:")
        for _, trade in loss_exits.iterrows():
            print(f"     {trade['symbol']}: {trade['action']} @ ₹{trade['price']}")
    
    # Check for pattern in heavy trading
    symbol_frequency = trades_df['symbol'].value_counts()
    heavy_traded = symbol_frequency[symbol_frequency > 4]
    
    print(f"\n📊 HEAVILY TRADED SYMBOLS (>4 trades):")
    for symbol, count in heavy_traded.items():
        print(f"   {symbol}: {count} trades")
    
    # Time analysis
    print(f"\n⏰ TRADING TIMELINE:")
    daily_trades = trades_df.groupby(trades_df['timestamp'].dt.date).size()
    for date, count in daily_trades.items():
        daily_amount = trades_df[trades_df['timestamp'].dt.date == date]['price'].sum()
        print(f"   {date}: {count} trades, ₹{daily_amount:,.0f} total volume")
    
    # Generate recommendations
    print(f"\n🎯 KEY FINDINGS & RECOMMENDATIONS:")
    print(f"=" * 50)
    
    loss_percentage = abs(unrealized_pnl) / initial_capital * 100
    
    if unrealized_pnl < 0:
        print(f"1. 🚨 CRITICAL: {loss_percentage:.1f}% capital loss detected")
        print(f"2. 💸 High charges (₹{total_charges:,.2f}) suggest overtrading")
        print(f"3. 📉 {len(loss_exits)} stop-loss exits indicate poor entry timing")
        print(f"4. 🔄 {len(positions_df)} open positions carry unrealized risk")
        
        print(f"\n🔧 IMMEDIATE ACTIONS NEEDED:")
        print(f"   • Reduce position sizes to limit losses")
        print(f"   • Implement stricter entry conditions")
        print(f"   • Review stop-loss levels (too tight?)")
        print(f"   • Consider closing losing positions")
        print(f"   • Analyze why {len(heavy_traded)} symbols traded heavily")
    
    conn.close()
    
    return {
        'initial_capital': initial_capital,
        'current_value': current_capital + total_position_value,
        'unrealized_pnl': unrealized_pnl,
        'loss_percentage': loss_percentage,
        'charges_paid': total_charges,
        'open_positions': len(positions_df),
        'stop_loss_exits': len(loss_exits)
    }

if __name__ == "__main__":
    result = calculate_real_pnl()
    
    # Save summary
    with open('real_pnl_analysis.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n💾 Analysis saved to: real_pnl_analysis.json")
