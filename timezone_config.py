# timezone_config.py
# Permanent timezone configuration for the trading bot

import os
import pytz
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

class TimezoneManager:
    """
    Centralized timezone management for the trading bot
    Ensures consistent IST timezone usage across all components
    """
    
    def __init__(self):
        self.IST = pytz.timezone('Asia/Kolkata')
        self.UTC = pytz.UTC
        self._setup_environment()
    
    def _setup_environment(self):
        """Set up environment variables for consistent timezone handling"""
        # Set TZ environment variable to IST
        os.environ['TZ'] = 'Asia/Kolkata'
        
        # Try to update system timezone (if possible)
        try:
            if hasattr(os, 'tzset'):
                os.tzset()
        except (AttributeError, OSError):
            # tzset not available on all systems
            pass
    
    def now_ist(self):
        """Get current time in IST"""
        return datetime.now(self.IST)
    
    def now_utc(self):
        """Get current time in UTC"""
        return datetime.now(self.UTC)
    
    def is_market_open(self, now=None):
        """
        Check if Indian stock market is currently open
        Market hours: 09:15 - 15:30 IST, Monday to Friday
        """
        if now is None:
            now = self.now_ist()
        
        # Ensure we have IST time
        if now.tzinfo is None:
            now = self.IST.localize(now)
        elif now.tzinfo != self.IST:
            now = now.astimezone(self.IST)
        
        # Check if it's a weekday (Monday=0, Sunday=6)
        if now.weekday() > 4:  # Saturday (5) or Sunday (6)
            return False
        
        # Check market hours
        market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return market_start <= now <= market_end
    
    def to_ist(self, dt):
        """Convert any datetime to IST"""
        if dt.tzinfo is None:
            # Naive datetime - assume it's already IST
            return self.IST.localize(dt)
        else:
            # Timezone-aware datetime - convert to IST
            return dt.astimezone(self.IST)
    
    def to_utc(self, dt):
        """Convert any datetime to UTC"""
        if dt.tzinfo is None:
            # Naive datetime - assume it's IST
            dt = self.IST.localize(dt)
        return dt.astimezone(self.UTC)
    
    def market_status_info(self):
        """Get comprehensive market status information"""
        now = self.now_ist()
        is_open = self.is_market_open(now)
        
        market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return {
            'current_time_ist': now,
            'current_time_utc': self.now_utc(),
            'is_market_open': is_open,
            'market_start': market_start,
            'market_end': market_end,
            'is_weekend': now.weekday() > 4,
            'timezone_offset': now.strftime('%z'),
            'timezone_name': now.strftime('%Z')
        }
    
    def log_timezone_info(self):
        """Log current timezone configuration for debugging"""
        status = self.market_status_info()
        logger.info("🌍 Timezone Configuration:")
        logger.info(f"   Current IST: {status['current_time_ist'].strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"   Current UTC: {status['current_time_utc'].strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"   Market Status: {'🟢 OPEN' if status['is_market_open'] else '🔴 CLOSED'}")
        logger.info(f"   Market Hours: {status['market_start'].strftime('%H:%M')} - {status['market_end'].strftime('%H:%M')} IST")
        logger.info(f"   Environment TZ: {os.environ.get('TZ', 'Not set')}")

# Create global timezone manager instance
timezone_manager = TimezoneManager()

# Convenience functions for easy import
def now_ist():
    """Get current IST time"""
    return timezone_manager.now_ist()

def now_utc():
    """Get current UTC time"""
    return timezone_manager.now_utc()

def is_market_open():
    """Check if market is currently open"""
    return timezone_manager.is_market_open()

def to_ist(dt):
    """Convert datetime to IST"""
    return timezone_manager.to_ist(dt)

def to_utc(dt):
    """Convert datetime to UTC"""
    return timezone_manager.to_utc(dt)

def get_market_status():
    """Get comprehensive market status"""
    return timezone_manager.market_status_info()

if __name__ == "__main__":
    # Test the timezone configuration
    print("🌍 TIMEZONE CONFIGURATION TEST")
    print("=" * 50)
    
    tm = TimezoneManager()
    tm.log_timezone_info()
    
    status = tm.market_status_info()
    print(f"\nMarket Status: {'🟢 OPEN' if status['is_market_open'] else '🔴 CLOSED'}")
    print(f"IST Time: {status['current_time_ist']}")
    print(f"UTC Time: {status['current_time_utc']}")
