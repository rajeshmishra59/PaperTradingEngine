#!/usr/bin/env python3
"""
BACKGROUND OPTIMIZER MONITOR
Monitor the background optimization process and provide real-time updates
"""

import time
import subprocess
import os
from datetime import datetime
import json
import signal
import sys

class OptimizerMonitor:
    """Monitor background optimizer process"""
    
    def __init__(self):
        self.log_file = 'optimizer_background.log'
        self.status_file = 'optimizer_status.json'
        self.pid_file = 'optimizer.pid'
        
    def check_process_status(self):
        """Check if optimizer is still running"""
        try:
            result = subprocess.run(['pgrep', '-f', 'retrain_optimizer.py'], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                pid = result.stdout.strip()
                return True, pid
            return False, None
        except:
            return False, None
    
    def get_cpu_usage(self, pid):
        """Get CPU usage of the process"""
        try:
            result = subprocess.run(['ps', '-p', pid, '-o', '%cpu'], 
                                  capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                return float(lines[1])
            return 0.0
        except:
            return 0.0
    
    def get_log_tail(self, lines=10):
        """Get last few lines from log file"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    all_lines = f.readlines()
                    return ''.join(all_lines[-lines:])
            return "No log file found yet"
        except:
            return "Error reading log file"
    
    def estimate_completion_time(self):
        """Estimate when optimization will complete"""
        # Based on our previous analysis: 250 combinations × 30 seconds ≈ 2+ hours
        # But let's check actual progress from log
        log_content = self.get_log_tail(50)
        
        # Look for progress indicators in log
        if "Strategy:" in log_content and "combination" in log_content.lower():
            # Try to extract current combination number
            lines = log_content.split('\n')
            for line in reversed(lines):
                if 'combination' in line.lower() or 'testing' in line.lower():
                    # Extract numbers if possible
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        current = int(numbers[0])
                        total = 250  # Approximate total combinations
                        progress = (current / total) * 100
                        remaining_time = ((total - current) * 30) / 60  # minutes
                        return progress, remaining_time
        
        return 0, 120  # Default: 0% progress, 2 hours remaining
    
    def create_status_report(self):
        """Create comprehensive status report"""
        is_running, pid = self.check_process_status()
        
        if is_running:
            cpu_usage = self.get_cpu_usage(pid)
            progress, eta_minutes = self.estimate_completion_time()
            recent_log = self.get_log_tail(5)
            
            status = {
                'timestamp': datetime.now().isoformat(),
                'status': 'RUNNING',
                'pid': pid,
                'cpu_usage': cpu_usage,
                'progress_percent': progress,
                'eta_minutes': eta_minutes,
                'eta_completion': (datetime.now().timestamp() + eta_minutes * 60),
                'recent_activity': recent_log.strip()
            }
        else:
            # Check if completed or failed
            recent_log = self.get_log_tail(10)
            if 'completed' in recent_log.lower() or 'finished' in recent_log.lower():
                status = {
                    'timestamp': datetime.now().isoformat(),
                    'status': 'COMPLETED',
                    'recent_activity': recent_log.strip()
                }
            else:
                status = {
                    'timestamp': datetime.now().isoformat(),
                    'status': 'STOPPED/FAILED',
                    'recent_activity': recent_log.strip()
                }
        
        return status
    
    def display_status(self):
        """Display current status"""
        status = self.create_status_report()
        
        print(f"\n🔍 BACKGROUND OPTIMIZER STATUS - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        
        if status['status'] == 'RUNNING':
            print(f"✅ Status: {status['status']} (PID: {status['pid']})")
            print(f"🖥️  CPU Usage: {status['cpu_usage']:.1f}%")
            print(f"📊 Progress: {status['progress_percent']:.1f}%")
            print(f"⏰ ETA: {status['eta_minutes']:.0f} minutes")
            
            completion_time = datetime.fromtimestamp(status['eta_completion'])
            print(f"🎯 Expected Completion: {completion_time.strftime('%H:%M:%S')}")
            
        elif status['status'] == 'COMPLETED':
            print(f"🎉 Status: OPTIMIZATION COMPLETED!")
            
        else:
            print(f"❌ Status: {status['status']}")
        
        print(f"\n📝 Recent Activity:")
        recent_lines = status['recent_activity'].split('\n')[-3:]
        for line in recent_lines:
            if line.strip():
                print(f"   {line.strip()}")
        
        return status
    
    def save_status(self, status):
        """Save status to file"""
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2)
    
    def monitor_loop(self, duration_minutes=10):
        """Monitor for specified duration"""
        print(f"🚀 STARTING OPTIMIZER MONITORING FOR {duration_minutes} MINUTES")
        print("=" * 60)
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while time.time() < end_time:
            try:
                status = self.display_status()
                self.save_status(status)
                
                if status['status'] == 'COMPLETED':
                    print(f"\n🎉 OPTIMIZATION COMPLETED! Monitoring stopped.")
                    break
                elif status['status'] == 'STOPPED/FAILED':
                    print(f"\n❌ OPTIMIZATION STOPPED/FAILED! Check logs.")
                    break
                
                print(f"\n⏳ Next update in 30 seconds... (Ctrl+C to stop monitoring)")
                time.sleep(30)
                
            except KeyboardInterrupt:
                print(f"\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                time.sleep(30)
        
        print(f"\n📋 Final Status:")
        final_status = self.display_status()
        self.save_status(final_status)
        
        if final_status['status'] == 'RUNNING':
            print(f"\n💡 Optimizer is still running in background.")
            print(f"   Check progress anytime with: python3 optimizer_monitor.py")
            print(f"   View logs with: tail -f optimizer_background.log")

def main():
    """Main monitoring function"""
    monitor = OptimizerMonitor()
    
    # Single status check
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        monitor.display_status()
        return
    
    # Full monitoring
    monitor.monitor_loop(duration_minutes=10)

if __name__ == "__main__":
    main()
