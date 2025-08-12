#!/usr/bin/env python3
"""
SMART DAILY RETRAINING - Realistic Approach
Har din sirf selected strategies aur top symbols optimize karta hai
"""

import yaml
import json
from datetime import datetime
import os

def get_today_strategy():
    """Aaj konsa strategy optimize karna hai"""
    weekday = datetime.now().weekday()  # 0=Monday, 4=Friday
    
    schedule = {
        0: "AlphaOneStrategy",    # Monday
        1: "ApexStrategy",        # Tuesday  
        2: "NumeroUnoStrategy",   # Wednesday
        3: "SankhyaEkStrategy",   # Thursday
        4: "TestStrategy"         # Friday
    }
    
    return schedule.get(weekday, "AlphaOneStrategy")

def create_daily_config():
    """Daily config banata hai"""
    today_strategy = get_today_strategy()
    
    # Top 10 symbols only
    top_symbols = [
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK",
        "HINDUNILVR", "SBIN", "ITC", "BHARTIARTL", "KOTAKBANK"
    ]
    
    # Original config load karo
    with open('config.yml', 'r') as f:
        full_config = yaml.safe_load(f)
    
    # Smart config banao
    smart_config = full_config.copy()
    
    # Sirf aaj ka strategy active rakhein
    smart_config['strategy_config'] = {
        today_strategy: {
            **full_config['strategy_config'][today_strategy],
            'symbols': top_symbols  # Top 10 symbols only
        }
    }
    
    # Save daily config
    with open('daily_config.yml', 'w') as f:
        yaml.dump(smart_config, f, default_flow_style=False)
    
    print(f"📅 Today ({datetime.now().strftime('%A')}): Optimizing {today_strategy}")
    print(f"🎯 Symbols: {len(top_symbols)} (instead of 50)")
    print(f"⏱️  Expected time: ~5-10 minutes (instead of 2+ hours)")
    
    return today_strategy, len(top_symbols)

if __name__ == "__main__":
    strategy, symbol_count = create_daily_config()
    
    # Timing calculation
    estimated_time = symbol_count * 30  # 30 seconds per symbol
    print(f"\n⚡ REALISTIC TIMING:")
    print(f"1 strategy × {symbol_count} symbols × ~30 secs = {estimated_time} seconds")
    print(f"= {estimated_time/60:.1f} minutes ✅")
