#!/usr/bin/env python3
"""
COMPREHENSIVE TRADE ANALYSIS
Analyze trade database to understand PnL patterns, win/loss ratios, and performance issues
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

class TradeAnalyzer:
    """
    Comprehensive trade analysis system to identify performance issues
    """
    
    def __init__(self, db_path: str = 'trading_data.db'):
        self.db_path = db_path
        self.conn = None
        self.trades_df = None
        
    def connect_db(self):
        """Connect to trading database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"✅ Connected to database: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def load_trades_data(self) -> pd.DataFrame:
        """Load all trades data from database"""
        if not self.connect_db():
            return pd.DataFrame()
        
        try:
            # Get table structure first
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"📊 Available tables: {[table[0] for table in tables]}")
            
            # Try to load trades data
            query = """
            SELECT * FROM trades 
            ORDER BY timestamp DESC
            """
            
            self.trades_df = pd.read_sql_query(query, self.conn)
            print(f"📈 Loaded {len(self.trades_df)} trade records")
            
            return self.trades_df
            
        except Exception as e:
            print(f"❌ Error loading trades data: {e}")
            
            # Try alternative table names
            alternative_queries = [
                "SELECT * FROM trade_log ORDER BY timestamp DESC",
                "SELECT * FROM trading_log ORDER BY timestamp DESC",
                "SELECT * FROM positions ORDER BY timestamp DESC"
            ]
            
            for query in alternative_queries:
                try:
                    self.trades_df = pd.read_sql_query(query, self.conn)
                    print(f"✅ Loaded data from alternative query: {len(self.trades_df)} records")
                    return self.trades_df
                except:
                    continue
            
            print("❌ Could not load trade data from any table")
            return pd.DataFrame()
    
    def analyze_database_structure(self):
        """Analyze database structure to understand available data"""
        if not self.connect_db():
            return
        
        cursor = self.conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("🔍 DATABASE STRUCTURE ANALYSIS")
        print("=" * 50)
        
        for table_name in tables:
            table = table_name[0]
            print(f"\n📊 Table: {table}")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            print("   Columns:")
            for col in columns:
                print(f"     • {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   Records: {count}")
            
            # Show sample data if exists
            if count > 0:
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                sample_data = cursor.fetchall()
                print("   Sample data:")
                for i, row in enumerate(sample_data):
                    print(f"     Row {i+1}: {row}")
    
    def comprehensive_pnl_analysis(self) -> Dict:
        """Comprehensive PnL analysis"""
        if self.trades_df is None or self.trades_df.empty:
            print("❌ No trade data available for analysis")
            return {}
        
        print("\n💰 COMPREHENSIVE PnL ANALYSIS")
        print("=" * 50)
        
        df = self.trades_df.copy()
        
        # Identify PnL column
        pnl_columns = [col for col in df.columns if 'pnl' in col.lower() or 'profit' in col.lower() or 'loss' in col.lower()]
        print(f"🔍 Potential PnL columns: {pnl_columns}")
        
        if not pnl_columns:
            print("❌ No PnL columns found in data")
            return {}
        
        # Use the first PnL column found
        pnl_col = pnl_columns[0]
        print(f"📊 Using PnL column: {pnl_col}")
        
        # Convert to numeric if needed
        df[pnl_col] = pd.to_numeric(df[pnl_col], errors='coerce')
        
        # Basic PnL statistics
        total_pnl = df[pnl_col].sum()
        avg_pnl = df[pnl_col].mean()
        median_pnl = df[pnl_col].median()
        
        # Win/Loss analysis
        winning_trades = df[df[pnl_col] > 0]
        losing_trades = df[df[pnl_col] < 0]
        breakeven_trades = df[df[pnl_col] == 0]
        
        total_trades = len(df)
        winning_count = len(winning_trades)
        losing_count = len(losing_trades)
        breakeven_count = len(breakeven_trades)
        
        win_rate = (winning_count / total_trades) * 100 if total_trades > 0 else 0
        
        # Profit/Loss amounts
        total_profits = winning_trades[pnl_col].sum() if not winning_trades.empty else 0
        total_losses = losing_trades[pnl_col].sum() if not losing_trades.empty else 0
        
        avg_win = winning_trades[pnl_col].mean() if not winning_trades.empty else 0
        avg_loss = losing_trades[pnl_col].mean() if not losing_trades.empty else 0
        
        # Risk-reward ratio
        risk_reward_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        analysis = {
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'avg_pnl': avg_pnl,
            'median_pnl': median_pnl,
            'winning_trades': winning_count,
            'losing_trades': losing_count,
            'breakeven_trades': breakeven_count,
            'win_rate': win_rate,
            'total_profits': total_profits,
            'total_losses': abs(total_losses),
            'avg_win': avg_win,
            'avg_loss': abs(avg_loss),
            'risk_reward_ratio': risk_reward_ratio
        }
        
        # Display results
        print(f"\n📊 OVERALL PERFORMANCE:")
        print(f"   Total Trades: {total_trades}")
        print(f"   Total PnL: ₹{total_pnl:,.2f}")
        print(f"   Average PnL per trade: ₹{avg_pnl:,.2f}")
        print(f"   Median PnL: ₹{median_pnl:,.2f}")
        
        print(f"\n🎯 WIN/LOSS BREAKDOWN:")
        print(f"   Winning Trades: {winning_count} ({win_rate:.1f}%)")
        print(f"   Losing Trades: {losing_count} ({(losing_count/total_trades)*100:.1f}%)")
        print(f"   Breakeven Trades: {breakeven_count} ({(breakeven_count/total_trades)*100:.1f}%)")
        
        print(f"\n💰 PROFIT/LOSS ANALYSIS:")
        print(f"   Total Profits: ₹{total_profits:,.2f}")
        print(f"   Total Losses: ₹{abs(total_losses):,.2f}")
        print(f"   Average Win: ₹{avg_win:,.2f}")
        print(f"   Average Loss: ₹{abs(avg_loss):,.2f}")
        print(f"   Risk-Reward Ratio: {risk_reward_ratio:.2f}")
        
        return analysis
    
    def strategy_wise_analysis(self) -> Dict:
        """Analyze performance by strategy"""
        if self.trades_df is None or self.trades_df.empty:
            return {}
        
        print("\n🎯 STRATEGY-WISE ANALYSIS")
        print("=" * 50)
        
        df = self.trades_df.copy()
        
        # Find strategy column
        strategy_columns = [col for col in df.columns if 'strategy' in col.lower()]
        
        if not strategy_columns:
            print("❌ No strategy column found")
            return {}
        
        strategy_col = strategy_columns[0]
        pnl_col = [col for col in df.columns if 'pnl' in col.lower()][0]
        
        # Group by strategy
        strategy_analysis = {}
        
        for strategy in df[strategy_col].unique():
            strategy_trades = df[df[strategy_col] == strategy]
            
            if strategy_trades.empty:
                continue
            
            pnl_data = pd.to_numeric(strategy_trades[pnl_col], errors='coerce')
            
            total_trades = len(strategy_trades)
            total_pnl = pnl_data.sum()
            win_rate = (len(pnl_data[pnl_data > 0]) / total_trades) * 100
            avg_pnl = pnl_data.mean()
            
            strategy_analysis[strategy] = {
                'total_trades': total_trades,
                'total_pnl': total_pnl,
                'win_rate': win_rate,
                'avg_pnl': avg_pnl
            }
            
            print(f"\n📈 {strategy}:")
            print(f"   Trades: {total_trades}")
            print(f"   Total PnL: ₹{total_pnl:,.2f}")
            print(f"   Win Rate: {win_rate:.1f}%")
            print(f"   Avg PnL: ₹{avg_pnl:,.2f}")
        
        return strategy_analysis
    
    def symbol_wise_analysis(self) -> Dict:
        """Analyze performance by symbol"""
        if self.trades_df is None or self.trades_df.empty:
            return {}
        
        print("\n📊 SYMBOL-WISE ANALYSIS")
        print("=" * 50)
        
        df = self.trades_df.copy()
        
        # Find symbol column
        symbol_columns = [col for col in df.columns if 'symbol' in col.lower() or 'stock' in col.lower()]
        
        if not symbol_columns:
            print("❌ No symbol column found")
            return {}
        
        symbol_col = symbol_columns[0]
        pnl_col = [col for col in df.columns if 'pnl' in col.lower()][0]
        
        # Group by symbol
        symbol_analysis = df.groupby(symbol_col).agg({
            pnl_col: ['count', 'sum', 'mean']
        }).round(2)
        
        symbol_analysis.columns = ['Total_Trades', 'Total_PnL', 'Avg_PnL']
        symbol_analysis = symbol_analysis.sort_values('Total_PnL', ascending=False)
        
        print("\n🏆 TOP PERFORMING SYMBOLS:")
        print(symbol_analysis.head(10))
        
        print("\n📉 WORST PERFORMING SYMBOLS:")
        print(symbol_analysis.tail(10))
        
        return symbol_analysis.to_dict()
    
    def time_based_analysis(self) -> Dict:
        """Analyze performance by time periods"""
        if self.trades_df is None or self.trades_df.empty:
            return {}
        
        print("\n⏰ TIME-BASED ANALYSIS")
        print("=" * 50)
        
        df = self.trades_df.copy()
        
        # Find timestamp column
        time_columns = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
        
        if not time_columns:
            print("❌ No timestamp column found")
            return {}
        
        time_col = time_columns[0]
        pnl_col = [col for col in df.columns if 'pnl' in col.lower()][0]
        
        # Convert timestamp
        df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
        df['date'] = df[time_col].dt.date
        df['hour'] = df[time_col].dt.hour
        
        # Daily analysis
        daily_pnl = df.groupby('date')[pnl_col].sum().sort_index()
        
        print(f"\n📅 DAILY PnL (Last 10 days):")
        for date, pnl in daily_pnl.tail(10).items():
            print(f"   {date}: ₹{pnl:,.2f}")
        
        # Hourly analysis
        hourly_pnl = df.groupby('hour')[pnl_col].agg(['count', 'sum', 'mean']).round(2)
        hourly_pnl.columns = ['Trades', 'Total_PnL', 'Avg_PnL']
        
        print(f"\n🕐 HOURLY PERFORMANCE:")
        print(hourly_pnl)
        
        return {
            'daily_pnl': daily_pnl.to_dict(),
            'hourly_analysis': hourly_pnl.to_dict()
        }
    
    def identify_loss_patterns(self) -> Dict:
        """Identify patterns in losing trades"""
        if self.trades_df is None or self.trades_df.empty:
            return {}
        
        print("\n🔍 LOSS PATTERN ANALYSIS")
        print("=" * 50)
        
        df = self.trades_df.copy()
        pnl_col = [col for col in df.columns if 'pnl' in col.lower()][0]
        
        # Convert PnL to numeric
        df[pnl_col] = pd.to_numeric(df[pnl_col], errors='coerce')
        
        # Identify losing trades
        losing_trades = df[df[pnl_col] < 0].copy()
        
        if losing_trades.empty:
            print("✅ No losing trades found!")
            return {}
        
        print(f"📊 Total losing trades: {len(losing_trades)}")
        print(f"💸 Total losses: ₹{abs(losing_trades[pnl_col].sum()):,.2f}")
        print(f"📉 Average loss: ₹{abs(losing_trades[pnl_col].mean()):,.2f}")
        print(f"📉 Median loss: ₹{abs(losing_trades[pnl_col].median()):,.2f}")
        print(f"📉 Largest loss: ₹{abs(losing_trades[pnl_col].min()):,.2f}")
        
        # Analyze loss distribution
        loss_ranges = {
            'Small (0-100)': len(losing_trades[losing_trades[pnl_col] >= -100]),
            'Medium (100-500)': len(losing_trades[(losing_trades[pnl_col] < -100) & (losing_trades[pnl_col] >= -500)]),
            'Large (500-1000)': len(losing_trades[(losing_trades[pnl_col] < -500) & (losing_trades[pnl_col] >= -1000)]),
            'Very Large (>1000)': len(losing_trades[losing_trades[pnl_col] < -1000])
        }
        
        print(f"\n📊 LOSS DISTRIBUTION:")
        for range_name, count in loss_ranges.items():
            percentage = (count / len(losing_trades)) * 100
            print(f"   {range_name}: {count} trades ({percentage:.1f}%)")
        
        return {
            'total_losing_trades': len(losing_trades),
            'total_losses': abs(losing_trades[pnl_col].sum()),
            'avg_loss': abs(losing_trades[pnl_col].mean()),
            'loss_distribution': loss_ranges
        }
    
    def generate_recommendations(self, analysis_results: Dict) -> List[str]:
        """Generate improvement recommendations based on analysis"""
        recommendations = []
        
        if not analysis_results:
            return ["No analysis data available for recommendations"]
        
        # Analyze win rate
        win_rate = analysis_results.get('win_rate', 0)
        if win_rate < 40:
            recommendations.append("🎯 CRITICAL: Win rate too low (<40%). Review entry criteria and strategy logic.")
        elif win_rate < 50:
            recommendations.append("⚠️ Win rate needs improvement. Consider tightening entry conditions.")
        
        # Analyze risk-reward ratio
        rr_ratio = analysis_results.get('risk_reward_ratio', 0)
        if rr_ratio < 1.0:
            recommendations.append("📉 CRITICAL: Risk-reward ratio <1.0. Average losses exceed average wins.")
        elif rr_ratio < 1.5:
            recommendations.append("⚠️ Risk-reward ratio needs improvement. Consider wider targets or tighter stops.")
        
        # Analyze overall PnL
        total_pnl = analysis_results.get('total_pnl', 0)
        if total_pnl < 0:
            recommendations.append("🚨 CRITICAL: Overall PnL is negative. System needs major revision.")
        
        # Analyze average loss vs average win
        avg_win = analysis_results.get('avg_win', 0)
        avg_loss = analysis_results.get('avg_loss', 0)
        
        if avg_loss > avg_win:
            recommendations.append("💸 Average losses exceed average wins. Implement better stop-loss management.")
        
        # General recommendations
        if win_rate < 50 and rr_ratio < 1.5:
            recommendations.append("🔧 Consider implementing trend-following strategies during strong market moves.")
            recommendations.append("🔧 Implement dynamic position sizing based on market volatility.")
            recommendations.append("🔧 Add pre-market analysis to filter trades during uncertain conditions.")
        
        return recommendations
    
    def create_performance_report(self):
        """Create comprehensive performance report"""
        print("📊 GENERATING COMPREHENSIVE TRADE ANALYSIS REPORT")
        print("=" * 60)
        
        # Load data
        self.load_trades_data()
        
        if self.trades_df is None or self.trades_df.empty:
            print("❌ No trade data found. Analyzing database structure...")
            self.analyze_database_structure()
            return
        
        # Run all analyses
        pnl_analysis = self.comprehensive_pnl_analysis()
        strategy_analysis = self.strategy_wise_analysis()
        symbol_analysis = self.symbol_wise_analysis()
        time_analysis = self.time_based_analysis()
        loss_patterns = self.identify_loss_patterns()
        
        # Generate recommendations
        recommendations = self.generate_recommendations(pnl_analysis)
        
        print("\n🎯 IMPROVEMENT RECOMMENDATIONS")
        print("=" * 50)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'pnl_analysis': pnl_analysis,
            'strategy_analysis': strategy_analysis,
            'symbol_analysis': symbol_analysis,
            'time_analysis': time_analysis,
            'loss_patterns': loss_patterns,
            'recommendations': recommendations
        }
        
        with open('trade_analysis_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report saved to: trade_analysis_report.json")
        
        if self.conn:
            self.conn.close()

def main():
    """Main function"""
    analyzer = TradeAnalyzer()
    analyzer.create_performance_report()

if __name__ == "__main__":
    main()
