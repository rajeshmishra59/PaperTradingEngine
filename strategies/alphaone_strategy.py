# File: strategies/alphaone_strategy.py
# Production Grade Version 5.3 - Fully Patched

import pandas as pd
import numpy as np
import warnings
from .base_strategy import BaseStrategy

warnings.simplefilter(action='ignore', category=FutureWarning)

class AlphaOneStrategy(BaseStrategy):
    """
    AlphaOne Strategy (v5.3): Implements a simplified 2-stage exit strategy.
    """
    def __init__(self, df: pd.DataFrame, symbol: str = None, logger=None, 
                 primary_timeframe: int = 15, **kwargs):
        
        super().__init__(df, symbol=symbol, logger=logger, primary_timeframe=primary_timeframe)
        self.name = "AlphaOne"
        
        # Strategy-specific parameters
        self.STREAK_PERIOD_MIN = 8
        self.STRONG_CANDLE_RATIO = 0.7
        self.VOLUME_SPIKE_MULTIPLIER = 1.5
        self.TP1_RR_RATIO = 1.5
        self.TP2_RR_RATIO = 3.0
        
        self.log(f"AlphaOneStrategy (v5.3) initialized for {self.symbol}.")

    def calculate_indicators(self):
        """Resamples 1-min data to the primary timeframe for this strategy instance."""
        if self.df_1min_raw.empty:
            self.df = pd.DataFrame()
            return

        tf_string = f'{self.primary_timeframe}T'
        self.df = self.df_1min_raw.resample(tf_string).agg(
            {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
        ).dropna()

    def generate_signals(self):
        """Generates trading signals based on the strategy's logic."""
        df = self.df
        
        # --- FIX: Initialize columns at the very beginning ---
        df['entry_signal'] = 'NONE'
        df['exit_signal'] = 'NONE'
        df['stop_loss'] = np.nan
        df['target'] = np.nan
        df['tp1'] = np.nan
        
        if df.empty or len(df) < self.STREAK_PERIOD_MIN + 1:
            return

        is_down_streak_candle = df['close'] < df['close'].shift(1)
        is_up_streak_candle = df['close'] > df['close'].shift(1)
        is_green = df['close'] > df['open']
        is_red = df['close'] < df['open']
        candle_range = (df['high'] - df['low']).replace(0, np.nan)
        body_size = (df['close'] - df['open']).abs()
        is_strong = (body_size / candle_range) >= self.STRONG_CANDLE_RATIO
        volume_avg = df['volume'].rolling(window=20).mean()
        has_volume = df['volume'] > (volume_avg * self.VOLUME_SPIKE_MULTIPLIER)

        required_streak = self.STREAK_PERIOD_MIN
        down_streak_active = is_down_streak_candle.rolling(window=required_streak).sum() == required_streak
        up_streak_active = is_up_streak_candle.rolling(window=required_streak).sum() == required_streak

        long_entry_cond = down_streak_active.shift(1) & is_green & is_strong & has_volume
        short_entry_cond = up_streak_active.shift(1) & is_red & is_strong & has_volume

        df.loc[long_entry_cond, 'entry_signal'] = 'LONG'
        df.loc[long_entry_cond, 'stop_loss'] = df['low']
        risk_long = df['close'] - df['stop_loss']
        df.loc[long_entry_cond, 'tp1'] = df['close'] + (risk_long * self.TP1_RR_RATIO)
        df.loc[long_entry_cond, 'target'] = df['close'] + (risk_long * self.TP2_RR_RATIO)
        
        df.loc[short_entry_cond, 'entry_signal'] = 'SHORT'
        df.loc[short_entry_cond, 'stop_loss'] = df['high']
        risk_short = df['stop_loss'] - df['close']
        df.loc[short_entry_cond, 'tp1'] = df['close'] - (risk_short * self.TP1_RR_RATIO)
        df.loc[short_entry_cond, 'target'] = df['close'] - (risk_short * self.TP2_RR_RATIO)