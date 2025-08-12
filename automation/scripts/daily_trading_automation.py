#!/usr/bin/env python3
"""
Daily Trading Automation Script
Runs retrain optimizer followed by paper trading system
"""

import os
import sys
import subprocess
import logging
import time
from datetime import datetime
import signal

# Setup logging
log_dir = "/home/ubuntu/PaperTradingV1.3/logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"automation_{datetime.now().strftime('%Y-%m-%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Global variable to track running processes
running_processes = []

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    logger.info("Received termination signal. Cleaning up...")
    for process in running_processes:
        if process.poll() is None:  # Process is still running
            logger.info(f"Terminating process {process.pid}")
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing process {process.pid}")
                process.kill()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def run_retrain_optimizer():
    """Run the retrain optimizer"""
    logger.info("🔧 Starting Retrain Optimizer...")
    
    try:
        # Change to the correct directory
        os.chdir("/home/ubuntu/PaperTradingV1.3")
        
        # Run retrain optimizer
        process = subprocess.run([
            sys.executable, "retrain_optimizer.py"
        ], capture_output=True, text=True, timeout=3600)  # 1 hour timeout
        
        if process.returncode == 0:
            logger.info("✅ Retrain Optimizer completed successfully")
            logger.info(f"Output: {process.stdout}")
            return True
        else:
            logger.error(f"❌ Retrain Optimizer failed with return code {process.returncode}")
            logger.error(f"Error: {process.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Retrain Optimizer timed out (1 hour limit)")
        return False
    except Exception as e:
        logger.error(f"❌ Error running retrain optimizer: {str(e)}")
        return False

def run_paper_trading():
    """Run the paper trading system"""
    logger.info("📈 Starting Paper Trading System...")
    
    try:
        # Change to the correct directory
        os.chdir("/home/ubuntu/PaperTradingV1.3")
        
        # Start paper trading as a background process
        process = subprocess.Popen([
            sys.executable, "main_papertrader.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        running_processes.append(process)
        
        logger.info(f"✅ Paper Trading System started with PID: {process.pid}")
        logger.info("📊 Paper trading will run until market close or manual termination")
        
        # Monitor the process
        while process.poll() is None:
            time.sleep(60)  # Check every minute
            logger.info("📈 Paper trading system is running...")
        
        # Process has ended
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            logger.info("✅ Paper Trading System completed successfully")
        else:
            logger.error(f"❌ Paper Trading System ended with return code {process.returncode}")
            if stderr:
                logger.error(f"Error: {stderr}")
        
        return process.returncode == 0
        
    except Exception as e:
        logger.error(f"❌ Error running paper trading: {str(e)}")
        return False

def check_market_time():
    """Check if it's a valid trading day and time"""
    now = datetime.now()
    
    # Check if it's a weekday (Monday=0, Sunday=6)
    if now.weekday() > 4:  # Saturday or Sunday
        logger.info("📅 Today is a weekend. Skipping trading automation.")
        return False
    
    # Check if it's within reasonable hours (8 AM to 4 PM)
    if now.hour < 8 or now.hour > 16:
        logger.info(f"⏰ Current time {now.strftime('%H:%M')} is outside trading hours. Skipping.")
        return False
    
    return True

def main():
    """Main automation function"""
    logger.info("🚀 Daily Trading Automation Started")
    logger.info(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if it's a valid trading time
    if not check_market_time():
        return
    
    # Step 1: Run retrain optimizer
    logger.info("=" * 50)
    logger.info("STEP 1: RETRAIN OPTIMIZER")
    logger.info("=" * 50)
    
    optimizer_success = run_retrain_optimizer()
    
    if optimizer_success:
        logger.info("✅ Retrain optimizer completed successfully. Proceeding to paper trading.")
    else:
        logger.warning("⚠️ Retrain optimizer failed, but continuing with paper trading using existing parameters.")
    
    # Wait a bit before starting paper trading
    time.sleep(5)
    
    # Step 2: Run paper trading
    logger.info("=" * 50)
    logger.info("STEP 2: PAPER TRADING")
    logger.info("=" * 50)
    
    trading_success = run_paper_trading()
    
    # Final status
    logger.info("=" * 50)
    logger.info("AUTOMATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Retrain Optimizer: {'✅ SUCCESS' if optimizer_success else '❌ FAILED'}")
    logger.info(f"Paper Trading: {'✅ SUCCESS' if trading_success else '❌ FAILED'}")
    logger.info("🏁 Daily trading automation completed")

if __name__ == "__main__":
    main()
