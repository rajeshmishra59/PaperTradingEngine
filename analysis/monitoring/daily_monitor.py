#!/usr/bin/env python3
"""
DAILY TRADING MONITOR
Real-time monitoring system to prevent overtrading and losses
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime, date
import time
from typing import Dict, List

class DailyTradingMonitor:
    """
    Real-time monitoring system to track daily trading activity and prevent overtrading
    """
    
    def __init__(self, db_path: str = 'trading_data.db'):
        self.db_path = db_path
        self.alerts = []
        self.daily_limits = {
            'max_trades': 10,
            'max_position_size': 2500,
            'max_symbols': 8,
            'daily_loss_limit': 500,
            'max_charges': 50
        }
        
    def get_today_stats(self) -> Dict:
        """Get today's trading statistics"""
        conn = sqlite3.connect(self.db_path)
        today = date.today().isoformat()
        
        # Get today's trades
        query = """
        SELECT * FROM trades 
        WHERE date(timestamp) = ? 
        ORDER BY timestamp
        """
        
        try:
            today_trades = pd.read_sql_query(query, conn, params=[today])
        except:
            today_trades = pd.DataFrame()
        
        if today_trades.empty:
            return {
                'total_trades': 0,
                'symbols_traded': 0,
                'largest_position': 0,
                'total_volume': 0,
                'estimated_charges': 0,
                'last_trade_time': None
            }
        
        # Calculate statistics
        total_trades = len(today_trades)
        symbols_traded = today_trades['symbol'].nunique()
        
        # Calculate position sizes
        today_trades['position_value'] = today_trades['price'] * today_trades['quantity']
        largest_position = today_trades['position_value'].max()
        total_volume = today_trades['position_value'].sum()
        
        # Estimate charges (0.1% of volume)
        estimated_charges = total_volume * 0.001
        
        # Last trade time
        last_trade_time = today_trades['timestamp'].iloc[-1] if len(today_trades) > 0 else None
        
        conn.close()
        
        return {
            'total_trades': total_trades,
            'symbols_traded': symbols_traded,
            'largest_position': largest_position,
            'total_volume': total_volume,
            'estimated_charges': estimated_charges,
            'last_trade_time': last_trade_time
        }
    
    def check_alerts(self, stats: Dict) -> List[str]:
        """Check for alert conditions"""
        alerts = []
        
        # Trade count alert
        if stats['total_trades'] >= self.daily_limits['max_trades']:
            alerts.append(f"🚨 TRADE LIMIT EXCEEDED: {stats['total_trades']}/{self.daily_limits['max_trades']}")
        elif stats['total_trades'] >= self.daily_limits['max_trades'] * 0.8:
            alerts.append(f"⚠️ APPROACHING TRADE LIMIT: {stats['total_trades']}/{self.daily_limits['max_trades']}")
        
        # Position size alert
        if stats['largest_position'] > self.daily_limits['max_position_size']:
            alerts.append(f"🚨 POSITION SIZE EXCEEDED: ₹{stats['largest_position']:,.0f}")
        
        # Symbol diversity alert
        if stats['symbols_traded'] > self.daily_limits['max_symbols']:
            alerts.append(f"⚠️ TOO MANY SYMBOLS: {stats['symbols_traded']}/{self.daily_limits['max_symbols']}")
        
        # Charges alert
        if stats['estimated_charges'] > self.daily_limits['max_charges']:
            alerts.append(f"💸 HIGH CHARGES: ₹{stats['estimated_charges']:,.0f}")
        
        return alerts
    
    def generate_daily_report(self) -> str:
        """Generate comprehensive daily report"""
        stats = self.get_today_stats()
        alerts = self.check_alerts(stats)
        
        report = f"""
📊 DAILY TRADING MONITOR - {date.today()}
{'=' * 50}

📈 TODAY'S STATISTICS:
   Total Trades: {stats['total_trades']}/{self.daily_limits['max_trades']}
   Symbols Traded: {stats['symbols_traded']}/{self.daily_limits['max_symbols']}
   Largest Position: ₹{stats['largest_position']:,.0f}
   Total Volume: ₹{stats['total_volume']:,.0f}
   Estimated Charges: ₹{stats['estimated_charges']:,.2f}
"""
        
        if stats['last_trade_time']:
            report += f"   Last Trade: {stats['last_trade_time']}\n"
        
        # Traffic light system
        if stats['total_trades'] < self.daily_limits['max_trades'] * 0.5:
            status = "🟢 SAFE"
        elif stats['total_trades'] < self.daily_limits['max_trades'] * 0.8:
            status = "🟡 CAUTION"
        else:
            status = "🔴 DANGER"
        
        report += f"\n🚦 STATUS: {status}\n"
        
        # Alerts section
        if alerts:
            report += f"\n🚨 ALERTS:\n"
            for alert in alerts:
                report += f"   {alert}\n"
        else:
            report += f"\n✅ NO ALERTS\n"
        
        # Recommendations
        remaining_trades = self.daily_limits['max_trades'] - stats['total_trades']
        if remaining_trades > 0:
            report += f"\n💡 REMAINING QUOTA: {remaining_trades} trades allowed today\n"
        else:
            report += f"\n🛑 TRADING QUOTA EXHAUSTED - STOP TRADING\n"
        
        return report
    
    def should_allow_trade(self, symbol: str, position_size: float) -> tuple:
        """Check if a new trade should be allowed"""
        stats = self.get_today_stats()
        
        # Check trade count
        if stats['total_trades'] >= self.daily_limits['max_trades']:
            return False, "Daily trade limit reached"
        
        # Check position size
        if position_size > self.daily_limits['max_position_size']:
            return False, f"Position size too large: ₹{position_size:,.0f}"
        
        # Check symbol count
        if stats['symbols_traded'] >= self.daily_limits['max_symbols']:
            # Check if this is a new symbol
            conn = sqlite3.connect(self.db_path)
            today = date.today().isoformat()
            
            query = """
            SELECT DISTINCT symbol FROM trades 
            WHERE date(timestamp) = ?
            """
            today_symbols = pd.read_sql_query(query, conn, params=[today])['symbol'].tolist()
            conn.close()
            
            if symbol not in today_symbols:
                return False, f"Too many symbols traded today: {stats['symbols_traded']}"
        
        # Check estimated daily charges
        new_charges = stats['estimated_charges'] + (position_size * 0.001)
        if new_charges > self.daily_limits['max_charges']:
            return False, f"Daily charges limit would be exceeded: ₹{new_charges:.2f}"
        
        return True, "Trade allowed"
    
    def save_daily_report(self):
        """Save daily report to file"""
        report = self.generate_daily_report()
        stats = self.get_today_stats()
        
        # Save text report
        filename = f"daily_report_{date.today()}.txt"
        with open(filename, 'w') as f:
            f.write(report)
        
        # Save JSON data
        json_filename = f"daily_stats_{date.today()}.json"
        stats['date'] = date.today().isoformat()
        stats['alerts'] = self.check_alerts(stats)
        
        with open(json_filename, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        print(report)
        print(f"\n💾 Reports saved: {filename}, {json_filename}")
        
        return filename, json_filename

def main():
    """Main monitoring function"""
    monitor = DailyTradingMonitor()
    
    print("🚀 STARTING DAILY TRADING MONITOR")
    print("=" * 50)
    
    while True:
        try:
            # Generate and display report
            report = monitor.generate_daily_report()
            print(f"\n{report}")
            
            # Save report every hour
            current_time = datetime.now()
            if current_time.minute == 0:  # Top of the hour
                monitor.save_daily_report()
            
            # Sleep for 5 minutes before next check
            time.sleep(300)
            
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
            break
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            time.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    # Run once to see current status
    monitor = DailyTradingMonitor()
    monitor.save_daily_report()
