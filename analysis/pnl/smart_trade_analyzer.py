#!/usr/bin/env python3
"""
SMART TRADE PnL ANALYZER
Calculates PnL from entry/exit trades and analyzes performance patterns
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import json
from collections import defaultdict

class SmartTradeAnalyzer:
    """
    Smart analyzer that calculates PnL from trade pairs and analyzes performance
    """
    
    def __init__(self, db_path: str = 'trading_data.db'):
        self.db_path = db_path
        self.conn = None
        self.trades_df = None
        self.calculated_pnl = []
        
    def connect_db(self):
        """Connect to trading database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"✅ Connected to database: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def load_all_data(self):
        """Load all trading data"""
        if not self.connect_db():
            return False
        
        # Load trades
        self.trades_df = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp", self.conn)
        print(f"📊 Loaded {len(self.trades_df)} trade records")
        
        # Load portfolio state
        portfolio_df = pd.read_sql_query("SELECT * FROM portfolio_state", self.conn)
        print(f"💼 Portfolio states: {len(portfolio_df)}")
        
        # Load open positions
        positions_df = pd.read_sql_query("SELECT * FROM open_positions", self.conn)
        print(f"📈 Open positions: {len(positions_df)}")
        
        return True
    
    def calculate_trade_pnl(self):
        """Calculate PnL by matching LONG/SHORT pairs"""
        print(f"\n💰 CALCULATING PnL FROM TRADE PAIRS")
        print("=" * 50)
        
        df = self.trades_df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Group by strategy and symbol to match pairs
        pnl_data = []
        position_tracker = defaultdict(list)  # Track open positions
        
        for _, trade in df.iterrows():
            symbol = trade['symbol']
            strategy = trade['strategy_name']
            action = trade['action']
            price = trade['price']
            quantity = trade['quantity']
            timestamp = trade['timestamp']
            
            key = f"{strategy}_{symbol}"
            
            if action == 'LONG':
                # Opening long position
                position_tracker[key].append({
                    'type': 'LONG',
                    'entry_price': price,
                    'quantity': quantity,
                    'entry_time': timestamp,
                    'trade_id': trade['id']
                })
                
            elif action == 'SHORT':
                # Closing long position (assuming SHORT means exit for long)
                if key in position_tracker and position_tracker[key]:
                    # Find matching long position (FIFO)
                    for i, pos in enumerate(position_tracker[key]):
                        if pos['type'] == 'LONG' and pos['quantity'] == quantity:
                            # Calculate PnL
                            entry_price = pos['entry_price']
                            exit_price = price
                            pnl = (exit_price - entry_price) * quantity
                            
                            # Calculate charges (approximate)
                            trade_value = max(entry_price * quantity, exit_price * quantity)
                            charges = trade_value * 0.001  # Approximate 0.1% charges
                            net_pnl = pnl - charges
                            
                            pnl_record = {
                                'strategy': strategy,
                                'symbol': symbol,
                                'entry_price': entry_price,
                                'exit_price': exit_price,
                                'quantity': quantity,
                                'gross_pnl': pnl,
                                'charges': charges,
                                'net_pnl': net_pnl,
                                'entry_time': pos['entry_time'],
                                'exit_time': timestamp,
                                'duration_minutes': (timestamp - pos['entry_time']).total_seconds() / 60,
                                'entry_trade_id': pos['trade_id'],
                                'exit_trade_id': trade['id']
                            }
                            
                            pnl_data.append(pnl_record)
                            
                            # Remove the matched position
                            position_tracker[key].pop(i)
                            break
        
        self.calculated_pnl = pnl_data
        print(f"✅ Calculated PnL for {len(pnl_data)} completed trades")
        
        # Show open positions (unmatched LONG trades)
        open_positions_count = sum(len(positions) for positions in position_tracker.values())
        print(f"📊 Open positions remaining: {open_positions_count}")
        
        return pnl_data
    
    def analyze_pnl_performance(self):
        """Comprehensive PnL analysis"""
        if not self.calculated_pnl:
            print("❌ No PnL data available. Run calculate_trade_pnl() first.")
            return
        
        print(f"\n🎯 COMPREHENSIVE PnL ANALYSIS")
        print("=" * 50)
        
        df = pd.DataFrame(self.calculated_pnl)
        
        if df.empty:
            print("❌ No completed trades found for PnL analysis")
            return
        
        # Basic statistics
        total_trades = len(df)
        total_gross_pnl = df['gross_pnl'].sum()
        total_charges = df['charges'].sum()
        total_net_pnl = df['net_pnl'].sum()
        
        avg_gross_pnl = df['gross_pnl'].mean()
        avg_net_pnl = df['net_pnl'].mean()
        
        # Win/Loss analysis
        winning_trades = df[df['net_pnl'] > 0]
        losing_trades = df[df['net_pnl'] < 0]
        breakeven_trades = df[df['net_pnl'] == 0]
        
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        breakeven_count = len(breakeven_trades)
        
        win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0
        
        # Profit/Loss amounts
        total_profits = winning_trades['net_pnl'].sum() if not winning_trades.empty else 0
        total_losses = abs(losing_trades['net_pnl'].sum()) if not losing_trades.empty else 0
        
        avg_win = winning_trades['net_pnl'].mean() if not winning_trades.empty else 0
        avg_loss = abs(losing_trades['net_pnl'].mean()) if not losing_trades.empty else 0
        
        # Risk-reward ratio
        risk_reward_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        # Display results
        print(f"📊 OVERALL PERFORMANCE:")
        print(f"   Total Completed Trades: {total_trades}")
        print(f"   Total Gross PnL: ₹{total_gross_pnl:,.2f}")
        print(f"   Total Charges: ₹{total_charges:,.2f}")
        print(f"   Total Net PnL: ₹{total_net_pnl:,.2f}")
        print(f"   Average Net PnL per trade: ₹{avg_net_pnl:,.2f}")
        
        print(f"\n🎯 WIN/LOSS BREAKDOWN:")
        print(f"   Winning Trades: {win_count} ({win_rate:.1f}%)")
        print(f"   Losing Trades: {loss_count} ({(loss_count/total_trades)*100:.1f}%)")
        print(f"   Breakeven Trades: {breakeven_count} ({(breakeven_count/total_trades)*100:.1f}%)")
        
        print(f"\n💰 PROFIT/LOSS ANALYSIS:")
        print(f"   Total Profits: ₹{total_profits:,.2f}")
        print(f"   Total Losses: ₹{total_losses:,.2f}")
        print(f"   Average Win: ₹{avg_win:,.2f}")
        print(f"   Average Loss: ₹{avg_loss:,.2f}")
        print(f"   Risk-Reward Ratio: {risk_reward_ratio:.2f}")
        
        if risk_reward_ratio < 1.0:
            print(f"   ⚠️ WARNING: Average losses exceed average wins!")
        
        if win_rate < 50:
            print(f"   ⚠️ WARNING: Win rate below 50%!")
        
        if total_net_pnl < 0:
            print(f"   🚨 CRITICAL: Overall PnL is NEGATIVE!")
        
        return {
            'total_trades': total_trades,
            'total_net_pnl': total_net_pnl,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'risk_reward_ratio': risk_reward_ratio,
            'total_profits': total_profits,
            'total_losses': total_losses
        }
    
    def strategy_performance(self):
        """Analyze performance by strategy"""
        if not self.calculated_pnl:
            return
        
        print(f"\n📈 STRATEGY-WISE PERFORMANCE")
        print("=" * 50)
        
        df = pd.DataFrame(self.calculated_pnl)
        
        strategy_stats = df.groupby('strategy').agg({
            'net_pnl': ['count', 'sum', 'mean'],
            'gross_pnl': 'sum',
            'charges': 'sum'
        }).round(2)
        
        strategy_stats.columns = ['Trades', 'Net_PnL', 'Avg_PnL', 'Gross_PnL', 'Charges']
        
        # Calculate win rates by strategy
        for strategy in df['strategy'].unique():
            strategy_trades = df[df['strategy'] == strategy]
            wins = len(strategy_trades[strategy_trades['net_pnl'] > 0])
            total = len(strategy_trades)
            win_rate = (wins / total) * 100 if total > 0 else 0
            strategy_stats.loc[strategy, 'Win_Rate'] = win_rate
        
        print(strategy_stats.sort_values('Net_PnL', ascending=False))
        
        return strategy_stats
    
    def symbol_performance(self):
        """Analyze performance by symbol"""
        if not self.calculated_pnl:
            return
        
        print(f"\n📊 SYMBOL-WISE PERFORMANCE")
        print("=" * 50)
        
        df = pd.DataFrame(self.calculated_pnl)
        
        symbol_stats = df.groupby('symbol').agg({
            'net_pnl': ['count', 'sum', 'mean'],
            'duration_minutes': 'mean'
        }).round(2)
        
        symbol_stats.columns = ['Trades', 'Total_PnL', 'Avg_PnL', 'Avg_Duration_Min']
        
        # Sort by total PnL
        symbol_stats = symbol_stats.sort_values('Total_PnL', ascending=False)
        
        print("🏆 TOP PERFORMING SYMBOLS:")
        print(symbol_stats.head(10))
        
        print("\n📉 WORST PERFORMING SYMBOLS:")
        print(symbol_stats.tail(10))
        
        return symbol_stats
    
    def identify_loss_patterns(self):
        """Identify patterns in losing trades"""
        if not self.calculated_pnl:
            return
        
        print(f"\n🔍 LOSS PATTERN ANALYSIS")
        print("=" * 50)
        
        df = pd.DataFrame(self.calculated_pnl)
        losing_trades = df[df['net_pnl'] < 0]
        
        if losing_trades.empty:
            print("✅ No losing trades found!")
            return
        
        total_losses = abs(losing_trades['net_pnl'].sum())
        avg_loss = abs(losing_trades['net_pnl'].mean())
        max_loss = abs(losing_trades['net_pnl'].min())
        
        print(f"📊 Total losing trades: {len(losing_trades)}")
        print(f"💸 Total losses: ₹{total_losses:,.2f}")
        print(f"📉 Average loss: ₹{avg_loss:,.2f}")
        print(f"📉 Maximum single loss: ₹{max_loss:,.2f}")
        
        # Loss by strategy
        loss_by_strategy = losing_trades.groupby('strategy')['net_pnl'].agg(['count', 'sum']).round(2)
        loss_by_strategy.columns = ['Loss_Count', 'Total_Loss']
        loss_by_strategy['Total_Loss'] = abs(loss_by_strategy['Total_Loss'])
        
        print(f"\n📉 LOSSES BY STRATEGY:")
        print(loss_by_strategy.sort_values('Total_Loss', ascending=False))
        
        # Loss by symbol
        loss_by_symbol = losing_trades.groupby('symbol')['net_pnl'].agg(['count', 'sum']).round(2)
        loss_by_symbol.columns = ['Loss_Count', 'Total_Loss']
        loss_by_symbol['Total_Loss'] = abs(loss_by_symbol['Total_Loss'])
        
        print(f"\n📉 WORST PERFORMING SYMBOLS (LOSSES):")
        print(loss_by_symbol.sort_values('Total_Loss', ascending=False).head(10))
        
        return {
            'total_losing_trades': len(losing_trades),
            'total_losses': total_losses,
            'avg_loss': avg_loss,
            'max_loss': max_loss
        }
    
    def generate_recommendations(self):
        """Generate actionable recommendations"""
        if not self.calculated_pnl:
            return []
        
        df = pd.DataFrame(self.calculated_pnl)
        
        total_pnl = df['net_pnl'].sum()
        win_rate = (len(df[df['net_pnl'] > 0]) / len(df)) * 100
        avg_win = df[df['net_pnl'] > 0]['net_pnl'].mean() if len(df[df['net_pnl'] > 0]) > 0 else 0
        avg_loss = abs(df[df['net_pnl'] < 0]['net_pnl'].mean()) if len(df[df['net_pnl'] < 0]) > 0 else 0
        rr_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        recommendations = []
        
        print(f"\n🎯 ACTIONABLE RECOMMENDATIONS")
        print("=" * 50)
        
        if total_pnl < 0:
            recommendations.append("🚨 URGENT: Overall PnL is negative. Review complete strategy logic.")
            
        if win_rate < 40:
            recommendations.append("🎯 CRITICAL: Win rate too low. Tighten entry conditions.")
            
        if rr_ratio < 1.0:
            recommendations.append("💸 CRITICAL: Average losses exceed wins. Improve stop-loss management.")
            
        if avg_loss > 100:
            recommendations.append("🛑 Consider reducing position sizes to limit large losses.")
            
        # Strategy-specific recommendations
        strategy_performance = df.groupby('strategy')['net_pnl'].sum()
        worst_strategy = strategy_performance.idxmin()
        worst_pnl = strategy_performance.min()
        
        if worst_pnl < -500:
            recommendations.append(f"⚠️ Strategy '{worst_strategy}' showing major losses (₹{abs(worst_pnl):,.2f}). Consider disabling.")
        
        # Symbol-specific recommendations
        symbol_performance = df.groupby('symbol')['net_pnl'].sum()
        worst_symbols = symbol_performance[symbol_performance < -200].index.tolist()
        
        if worst_symbols:
            recommendations.append(f"📉 Consider avoiding symbols: {', '.join(worst_symbols[:5])} (consistent losses)")
        
        # General recommendations
        if len(recommendations) == 0:
            recommendations.append("✅ Overall performance looks stable. Monitor for consistency.")
        else:
            recommendations.append("🔧 Implement pre-market analysis to filter trades during uncertain conditions.")
            recommendations.append("🔧 Consider implementing dynamic position sizing based on recent performance.")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        return recommendations
    
    def create_comprehensive_report(self):
        """Generate complete trading performance report"""
        print("🚀 COMPREHENSIVE TRADING PERFORMANCE ANALYSIS")
        print("=" * 60)
        
        # Load data
        if not self.load_all_data():
            return
        
        # Calculate PnL
        pnl_data = self.calculate_trade_pnl()
        
        if not pnl_data:
            print("❌ No completed trades found for analysis")
            return
        
        # Run all analyses
        overall_performance = self.analyze_pnl_performance()
        strategy_performance = self.strategy_performance()
        symbol_performance = self.symbol_performance()
        loss_patterns = self.identify_loss_patterns()
        recommendations = self.generate_recommendations()
        
        # Save detailed report
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_trades_analyzed': len(pnl_data),
            'overall_performance': overall_performance,
            'detailed_trades': pnl_data,
            'recommendations': recommendations
        }
        
        with open('comprehensive_trade_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report saved to: comprehensive_trade_report.json")
        
        # Summary
        print(f"\n📋 EXECUTIVE SUMMARY")
        print("=" * 50)
        if overall_performance:
            net_pnl = overall_performance.get('total_net_pnl', 0)
            win_rate = overall_performance.get('win_rate', 0)
            
            if net_pnl > 0:
                print(f"✅ Profitable: ₹{net_pnl:,.2f} profit with {win_rate:.1f}% win rate")
            else:
                print(f"❌ Loss-making: ₹{abs(net_pnl):,.2f} loss with {win_rate:.1f}% win rate")
                print(f"🔥 IMMEDIATE ACTION REQUIRED!")
        
        if self.conn:
            self.conn.close()

def main():
    """Main execution"""
    analyzer = SmartTradeAnalyzer()
    analyzer.create_comprehensive_report()

if __name__ == "__main__":
    main()
