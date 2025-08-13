#!/usr/bin/env python3

"""
Real-time Alert Dashboard for Paper Trading Bot
Background में चलने वाला monitoring dashboard
"""

import json
import time
import os
from datetime import datetime, timedelta
import subprocess
import threading
from collections import deque

class AlertDashboard:
    def __init__(self):
        self.script_dir = "/home/ubuntu/PaperTradingV1.3"
        self.status_file = f"{self.script_dir}/system_status.json"
        self.alert_log = f"{self.script_dir}/logs/alerts.log"
        self.running = True
        self.recent_alerts = deque(maxlen=50)
        
    def load_system_status(self):
        """Load current system status"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def get_recent_alerts(self):
        """Get recent alerts from log file"""
        try:
            if os.path.exists(self.alert_log):
                with open(self.alert_log, 'r') as f:
                    lines = f.readlines()
                    return lines[-10:]  # Last 10 alerts
        except:
            pass
        return []
    
    def send_webhook_alert(self, severity, message):
        """Send alert to webhook (you can configure this)"""
        # Example webhook integration
        # webhook_url = "https://your-webhook-url.com/alerts"
        # payload = {
        #     "severity": severity,
        #     "message": message,
        #     "timestamp": datetime.now().isoformat(),
        #     "system": "PaperTradingBot"
        # }
        # requests.post(webhook_url, json=payload)
        pass
    
    def display_status(self):
        """Display current system status"""
        os.system('clear')
        print("🔍 Paper Trading Bot - Live Alert Dashboard")
        print("=" * 60)
        print(f"🕒 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Load current status
        status = self.load_system_status()
        
        if status:
            print("📊 Current System Status:")
            print(f"   Market: {status.get('market_status', 'UNKNOWN')}")
            print(f"   Bot: {status.get('bot_status', 'UNKNOWN')}")
            print(f"   Broker: {status.get('broker_status', 'UNKNOWN')}")
            print(f"   Disk: {status.get('disk_usage', 'UNKNOWN')}")
            print(f"   Memory: {status.get('memory_usage', 'UNKNOWN')}")
            print(f"   Issues: {status.get('issues_count', 0)}")
            print(f"   Last Check: {status.get('last_check', 'UNKNOWN')}")
        else:
            print("⚠️  No status data available")
        
        print()
        print("🚨 Recent Alerts:")
        alerts = self.get_recent_alerts()
        if alerts:
            for alert in alerts[-5:]:  # Show last 5
                print(f"   {alert.strip()}")
        else:
            print("   ✅ No recent alerts")
        
        print()
        print("💡 Commands:")
        print("   Ctrl+C: Stop dashboard")
        print("   Check logs: tail -f logs/alerts.log")
        print("   System status: ./check_system_status.sh")
        
    def monitor_alerts(self):
        """Monitor for new alerts"""
        last_alert_count = 0
        
        while self.running:
            try:
                alerts = self.get_recent_alerts()
                current_count = len(alerts)
                
                if current_count > last_alert_count:
                    # New alert detected
                    new_alerts = alerts[last_alert_count:]
                    for alert in new_alerts:
                        if "[HIGH]" in alert or "[CRITICAL]" in alert:
                            # Send immediate notification for high/critical alerts
                            print(f"\n🚨 URGENT ALERT: {alert.strip()}")
                            self.send_webhook_alert("HIGH", alert.strip())
                
                last_alert_count = current_count
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Error monitoring alerts: {e}")
                time.sleep(30)
    
    def run(self):
        """Run the dashboard"""
        print("🚀 Starting Alert Dashboard...")
        
        # Start alert monitoring in background thread
        monitor_thread = threading.Thread(target=self.monitor_alerts)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        try:
            while self.running:
                self.display_status()
                time.sleep(30)  # Refresh every 30 seconds
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping Alert Dashboard...")
            self.running = False

if __name__ == "__main__":
    dashboard = AlertDashboard()
    dashboard.run()
