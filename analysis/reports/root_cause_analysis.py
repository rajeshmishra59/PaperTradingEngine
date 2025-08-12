#!/usr/bin/env python3
"""
PROBLEM ROOT CAUSE ANALYSIS
Deep analysis of what's causing losses and how to fix it
"""

import sqlite3
import pandas as pd
import json

def root_cause_analysis():
    """Identify root causes of trading losses"""
    
    print("🔍 ROOT CAUSE ANALYSIS - क्यों हो रहे हैं नुकसान?")
    print("=" * 60)
    
    conn = sqlite3.connect('trading_data.db')
    trades_df = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp", conn)
    trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
    
    # Problem 1: Overtrading Analysis
    print("🚨 PROBLEM 1: OVERTRADING")
    print("-" * 30)
    
    total_volume = (trades_df['price'] * trades_df['quantity']).sum()
    avg_trade_size = (trades_df['price'] * trades_df['quantity']).mean()
    
    print(f"   Total Trade Volume: ₹{total_volume:,.0f}")
    print(f"   Average Trade Size: ₹{avg_trade_size:,.0f}")
    print(f"   Trades in 2 days: {len(trades_df)}")
    print(f"   Trades per day: {len(trades_df)/2:.0f}")
    print(f"   ⚠️ TOO MUCH TRADING: {len(trades_df)} trades in just 2 days!")
    
    # Problem 2: Stop Loss Analysis
    print(f"\n🛑 PROBLEM 2: POOR STOP LOSS MANAGEMENT")
    print("-" * 40)
    
    stop_loss_trades = trades_df[trades_df['action'].str.contains('FINAL_EXIT_LOSS')]
    normal_exits = trades_df[trades_df['action'].str.contains('EXIT') & ~trades_df['action'].str.contains('FINAL_EXIT_LOSS')]
    
    stop_loss_rate = len(stop_loss_trades) / (len(stop_loss_trades) + len(normal_exits)) * 100
    
    print(f"   Stop Loss Exits: {len(stop_loss_trades)}")
    print(f"   Normal Exits: {len(normal_exits)}")
    print(f"   Stop Loss Rate: {stop_loss_rate:.1f}%")
    
    if stop_loss_rate > 10:
        print(f"   🚨 HIGH STOP LOSS RATE: {stop_loss_rate:.1f}% is too high!")
    
    # Problem 3: Heavy Trading Symbols
    print(f"\n🔄 PROBLEM 3: SYMBOL CONCENTRATION")
    print("-" * 35)
    
    symbol_trades = trades_df['symbol'].value_counts()
    heavy_symbols = symbol_trades[symbol_trades >= 4]
    
    print(f"   Heavily traded symbols ({len(heavy_symbols)}):")
    for symbol, count in heavy_symbols.items():
        symbol_data = trades_df[trades_df['symbol'] == symbol]
        volume = (symbol_data['price'] * symbol_data['quantity']).sum()
        print(f"     {symbol}: {count} trades, ₹{volume:,.0f} volume")
    
    # Problem 4: Timing Analysis
    print(f"\n⏰ PROBLEM 4: TRADING TIMING")
    print("-" * 30)
    
    trades_df['hour'] = trades_df['timestamp'].dt.hour
    hourly_trades = trades_df['hour'].value_counts().sort_index()
    
    print(f"   Trading hours distribution:")
    for hour, count in hourly_trades.items():
        if count > 5:  # Highlight heavy trading hours
            print(f"     {hour}:00 - {count} trades {'🔥' if count > 10 else ''}")
    
    # Problem 5: Position Size Analysis
    print(f"\n💰 PROBLEM 5: POSITION SIZING")
    print("-" * 30)
    
    trade_values = trades_df['price'] * trades_df['quantity']
    large_trades = trade_values[trade_values > 5000]
    
    print(f"   Large trades (>₹5000): {len(large_trades)}")
    print(f"   Largest trade: ₹{trade_values.max():,.0f}")
    print(f"   Average trade size: ₹{trade_values.mean():,.0f}")
    
    if trade_values.max() > 10000:
        print(f"   ⚠️ POSITION SIZES TOO LARGE for paper trading!")
    
    # Problem 6: Strategy Efficiency
    print(f"\n🎯 PROBLEM 6: STRATEGY EFFICIENCY")
    print("-" * 35)
    
    # Calculate win rate from normal exits
    profitable_actions = ['EXIT_SHORT', 'EXIT_LONG']  # Assuming these are profitable exits
    stop_loss_actions = ['FINAL_EXIT_LOSS_SHORT', 'FINAL_EXIT_LOSS_LONG']
    
    profitable_exits = len(trades_df[trades_df['action'].isin(profitable_actions)])
    loss_exits = len(trades_df[trades_df['action'].isin(stop_loss_actions)])
    
    if profitable_exits + loss_exits > 0:
        strategy_win_rate = profitable_exits / (profitable_exits + loss_exits) * 100
        print(f"   Profitable exits: {profitable_exits}")
        print(f"   Loss exits: {loss_exits}")
        print(f"   Strategy win rate: {strategy_win_rate:.1f}%")
        
        if strategy_win_rate < 70:
            print(f"   🚨 LOW WIN RATE: {strategy_win_rate:.1f}% is below acceptable level!")
    
    # Recommendations
    print(f"\n🔧 IMMEDIATE FIXES NEEDED:")
    print("=" * 50)
    
    recommendations = []
    
    if len(trades_df) > 50:
        recommendations.append("1. 🛑 REDUCE TRADING FREQUENCY: 54 trades/day is excessive")
    
    if stop_loss_rate > 10:
        recommendations.append("2. 📊 IMPROVE ENTRY TIMING: High stop-loss rate indicates poor entries")
    
    if trade_values.max() > 8000:
        recommendations.append("3. 💰 REDUCE POSITION SIZES: Large positions increase risk")
    
    if len(heavy_symbols) > 2:
        recommendations.append("4. 🎯 DIVERSIFY BETTER: Don't over-trade same symbols")
    
    recommendations.append("5. ⏰ IMPLEMENT PRE-MARKET ANALYSIS: Filter trades based on market conditions")
    recommendations.append("6. 🔄 WEEKLY ROTATION: Don't trade same symbols every day")
    
    for rec in recommendations:
        print(f"   {rec}")
    
    # Specific numbers for fixes
    print(f"\n📊 SUGGESTED IMPROVEMENTS:")
    print("-" * 30)
    print(f"   • Max trades per day: 10-15 (currently {len(trades_df)/2:.0f})")
    print(f"   • Max position size: ₹3000 (currently ₹{trade_values.max():,.0f})")
    print(f"   • Target win rate: 70%+ (currently {strategy_win_rate:.1f}%)")
    print(f"   • Max stop loss rate: 20% (currently {stop_loss_rate:.1f}%)")
    
    conn.close()
    
    return {
        'overtrading': len(trades_df) > 50,
        'high_stop_loss_rate': stop_loss_rate > 15,
        'large_positions': trade_values.max() > 8000,
        'low_win_rate': strategy_win_rate < 70,
        'recommendations': recommendations
    }

if __name__ == "__main__":
    analysis = root_cause_analysis()
    
    # Save analysis
    with open('root_cause_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    print(f"\n💾 Root cause analysis saved to: root_cause_analysis.json")
