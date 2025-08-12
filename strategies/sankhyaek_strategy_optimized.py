# File: strategies/sankhyaek_strategy_optimized.py (LOSS-PREVENTION VERSION)

import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import time, datetime
from typing import Optional
from .base_strategy import BaseStrategy

class SankhyaEkStrategy(BaseStrategy):
    def __init__(self, df: pd.DataFrame, symbol: Optional[str] = None, logger=None, 
                 primary_timeframe: int = 5, **kwargs):

        super().__init__(df, symbol=symbol, logger=logger, primary_timeframe=primary_timeframe)
        self.name = "SankhyaEkStrategy"
        
        # OPTIMIZED PARAMETERS TO PREVENT LOSSES
        self.bb_length, self.bb_std, self.rsi_period = 20, 2.0, 14  # More conservative
        self.rsi_oversold, self.rsi_overbought = 30, 70  # Tighter range
        self.stop_loss_pct, self.risk_reward_ratio = 0.01, 2.5  # Better R:R
        
        # TRADING LIMITS TO PREVENT OVERTRADING
        self.max_trades_per_day = 3  # Reduced from excessive trading
        self.max_position_size = 2500  # Max position size
        self.min_gap_between_trades = 15  # 15 minutes gap
        
        # Daily tracking
        self.last_trade_date = None
        self.signals_today = 0
        self.last_trade_time = None
        self.daily_trades = []
        
        # Time restrictions
        self.trade_start_time = time(9, 30)
        self.trade_stop_time = time(14, 30)  # Stop earlier
        self.avoid_volatile_hours = [time(12, 0), time(13, 0)]  # Lunch break
        
        self.log(f"Initialized OPTIMIZED {self.symbol} strategy with strict limits.")

    def calculate_indicators(self):
        if self.df_1min_raw.empty:
            self.log("Raw 1-minute data is empty.", level='warning')
            return

        tf_string = f'{self.primary_timeframe}T'
        resampled_df = self.df_1min_raw.resample(tf_string).agg(
            {'open':'first', 'high':'max', 'low':'min', 'close':'last', 'volume':'sum'}
        ).dropna()

        if len(resampled_df) < max(self.bb_length, 50):  # Need more data for reliability
            self.log(f"Insufficient data for reliable signals (need 50+, have {len(resampled_df)}).", level='warning')
            return
            
        # Calculate indicators with trend filter
        resampled_df.ta.bbands(length=self.bb_length, std=self.bb_std, append=True)
        resampled_df.ta.rsi(length=self.rsi_period, append=True)
        
        # Multiple trend filters for better accuracy
        resampled_df['ma_short'] = resampled_df['close'].rolling(20).mean()
        resampled_df['ma_long'] = resampled_df['close'].rolling(50).mean()
        resampled_df['trend_strength'] = (resampled_df['ma_short'] - resampled_df['ma_long']) / resampled_df['ma_long']
        
        # Volume filter
        resampled_df['volume_ma'] = resampled_df['volume'].rolling(20).mean()
        resampled_df['volume_ratio'] = resampled_df['volume'] / resampled_df['volume_ma']
        
        # Find actual column names
        bb_lower_col = next((col for col in resampled_df.columns if f'BBL_{self.bb_length}_' in col), None)
        bb_upper_col = next((col for col in resampled_df.columns if f'BBU_{self.bb_length}_' in col), None)
        rsi_col = next((col for col in resampled_df.columns if f'RSI_{self.rsi_period}' in col), None)
        
        rename_dict = {}
        if bb_lower_col: rename_dict[bb_lower_col] = 'bb_lower'
        if bb_upper_col: rename_dict[bb_upper_col] = 'bb_upper'
        if rsi_col: rename_dict[rsi_col] = 'rsi'
        
        if rename_dict:
            resampled_df.rename(columns=rename_dict, inplace=True)
            self.df = resampled_df
            self.log(f"Indicators calculated successfully with {len(self.df)} bars.")
        else:
            self.log("Failed to find indicator columns.", level='error')

    def can_trade_now(self):
        """Enhanced trading permission checker"""
        now = datetime.now().time()
        today = datetime.now().date()
        
        # Check time restrictions
        if now < self.trade_start_time or now > self.trade_stop_time:
            return False, "Outside trading hours"
        
        # Avoid volatile hours
        for avoid_time in self.avoid_volatile_hours:
            if avoid_time <= now <= time(avoid_time.hour + 1, 0):
                return False, "Avoiding volatile hours"
        
        # Reset daily counter if new day
        if self.last_trade_date != today:
            self.signals_today = 0
            self.daily_trades = []
            self.last_trade_date = today
            self.log(f"New trading day started. Reset counters.")
        
        # Check daily trade limit
        if self.signals_today >= self.max_trades_per_day:
            return False, f"Daily limit reached ({self.signals_today}/{self.max_trades_per_day})"
        
        # Check time gap between trades
        if self.last_trade_time:
            time_diff = (datetime.combine(today, now) - datetime.combine(today, self.last_trade_time)).seconds / 60
            if time_diff < self.min_gap_between_trades:
                return False, f"Minimum gap not met ({time_diff:.1f}/{self.min_gap_between_trades} min)"
        
        return True, "Trading allowed"

    def calculate_position_size(self, price):
        """Dynamic position sizing with strict limits"""
        base_size = 1500  # Base position size
        
        # Never exceed maximum position size
        max_quantity = int(self.max_position_size / price)
        base_quantity = int(base_size / price)
        
        # Use smaller of the two
        quantity = min(max_quantity, base_quantity)
        
        # Minimum viable quantity
        if quantity < 1:
            quantity = 1
        
        actual_size = quantity * price
        self.log(f"Position size: {quantity} shares = ₹{actual_size:,.0f} (limit: ₹{self.max_position_size})")
        
        return quantity

    def get_signals(self):
        if self.df is None or len(self.df) < 5:
            return "HOLD", 0

        # Check if trading is allowed
        can_trade, reason = self.can_trade_now()
        if not can_trade:
            return "HOLD", 0

        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        
        # Ensure all required columns exist
        required_cols = ['close', 'bb_lower', 'bb_upper', 'rsi', 'ma_short', 'ma_long', 'volume_ratio']
        if not all(col in self.df.columns for col in required_cols):
            return "HOLD", 0

        price = latest['close']
        
        # Enhanced signal conditions with multiple filters
        
        # LONG signal conditions (MORE STRICT)
        long_conditions = [
            price <= latest['bb_lower'],  # Price at lower BB
            latest['rsi'] <= self.rsi_oversold,  # RSI oversold
            latest['ma_short'] > latest['ma_long'],  # Short-term uptrend
            latest['volume_ratio'] > 1.2,  # Above average volume
            latest['close'] > prev['close'],  # Current bar bullish
        ]
        
        # SHORT signal conditions (MORE STRICT)
        short_conditions = [
            price >= latest['bb_upper'],  # Price at upper BB
            latest['rsi'] >= self.rsi_overbought,  # RSI overbought
            latest['ma_short'] < latest['ma_long'],  # Short-term downtrend
            latest['volume_ratio'] > 1.2,  # Above average volume
            latest['close'] < prev['close'],  # Current bar bearish
        ]
        
        # Require ALL conditions to be met (not just majority)
        if all(long_conditions):
            quantity = self.calculate_position_size(price)
            self.signals_today += 1
            self.last_trade_time = datetime.now().time()
            self.daily_trades.append(('LONG', price, quantity, datetime.now()))
            self.log(f"STRONG LONG signal: RSI={latest['rsi']:.1f}, BB position, trend aligned")
            return "LONG", quantity
            
        elif all(short_conditions):
            quantity = self.calculate_position_size(price)
            self.signals_today += 1
            self.last_trade_time = datetime.now().time()
            self.daily_trades.append(('SHORT', price, quantity, datetime.now()))
            self.log(f"STRONG SHORT signal: RSI={latest['rsi']:.1f}, BB position, trend aligned")
            return "SHORT", quantity

        return "HOLD", 0

    def get_stop_loss_price(self, entry_price, direction):
        """Conservative stop loss"""
        if direction == "LONG":
            return entry_price * (1 - self.stop_loss_pct)
        else:  # SHORT
            return entry_price * (1 + self.stop_loss_pct)

    def get_target_price(self, entry_price, direction):
        """Conservative target based on risk-reward ratio"""
        stop_loss_distance = entry_price * self.stop_loss_pct
        target_distance = stop_loss_distance * self.risk_reward_ratio
        
        if direction == "LONG":
            return entry_price + target_distance
        else:  # SHORT
            return entry_price - target_distance

    def should_exit_position(self, position, current_price):
        """Enhanced exit logic with time-based exits"""
        direction = position.get('action', '').upper()
        entry_price = position.get('entry_price', 0)
        entry_time = position.get('timestamp')
        
        if entry_price == 0:
            return True, "Invalid entry price"
        
        # Time-based exit (if position held too long)
        if entry_time:
            try:
                entry_dt = pd.to_datetime(entry_time)
                current_dt = pd.Timestamp.now()
                hours_held = (current_dt - entry_dt).total_seconds() / 3600
                
                if hours_held > 4:  # Exit if held more than 4 hours
                    return True, f"Time-based exit after {hours_held:.1f} hours"
            except:
                pass
        
        # Price-based exits
        stop_loss = self.get_stop_loss_price(entry_price, direction)
        target = self.get_target_price(entry_price, direction)
        
        if direction == "LONG":
            if current_price <= stop_loss:
                return True, f"Stop loss hit: {current_price:.2f} <= {stop_loss:.2f}"
            elif current_price >= target:
                return True, f"Target hit: {current_price:.2f} >= {target:.2f}"
        elif direction == "SHORT":
            if current_price >= stop_loss:
                return True, f"Stop loss hit: {current_price:.2f} >= {stop_loss:.2f}"
            elif current_price <= target:
                return True, f"Target hit: {current_price:.2f} <= {target:.2f}"
        
        return False, "Hold position"

    def log_daily_summary(self):
        """Log daily trading summary"""
        if self.daily_trades:
            self.log(f"Daily Summary: {len(self.daily_trades)} trades executed")
            for i, (action, price, qty, time) in enumerate(self.daily_trades, 1):
                self.log(f"  {i}. {action} {qty} @ ₹{price:.2f} at {time.strftime('%H:%M')}")
