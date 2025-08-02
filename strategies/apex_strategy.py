# File: strategies/apex_strategy.py
# Production Grade - Final Patch

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class ApexStrategy(BaseStrategy):
    """
    Apex Strategy (Triangle Breakout): Identifies contracting triangles and generates breakout signals.
    """
    def __init__(self, df: pd.DataFrame, symbol: str = None, logger=None,
                 primary_timeframe: int = 5, **kwargs):

        super().__init__(df, symbol=symbol, logger=logger, primary_timeframe=primary_timeframe)
        self.name = "Apex"
        
        # --- FIX: Yeh line jodna zaroori hai ---
        self.primary_timeframe = primary_timeframe
        
        # Strategy-specific parameters
        self.LOOKBACK_PERIOD = 10
        self.TP_RR_RATIO = 2.0
        
        self.log(f"ApexStrategy initialized for {self.symbol} with {self.primary_timeframe} min timeframe.")

    def calculate_indicators(self):
        """Resamples 1-min data and calculates rolling high/low."""
        if self.df_1min_raw.empty:
            self.df = pd.DataFrame()
            return

        tf_string = f'{self.primary_timeframe}T'
        self.df = self.df_1min_raw.resample(tf_string).agg(
            {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
        ).dropna()

        df = self.df
        if df.empty or len(df) < self.LOOKBACK_PERIOD: return

        df['rolling_high'] = df['high'].rolling(window=self.LOOKBACK_PERIOD).max().shift(1)
        df['rolling_low'] = df['low'].rolling(window=self.LOOKBACK_PERIOD).min().shift(1)
        
    def generate_signals(self):
        """Generates breakout signals."""
        df = self.df
        
        df['entry_signal'] = 'NONE'
        df['exit_signal'] = 'NONE'
        df['stop_loss'] = np.nan
        df['target'] = np.nan
        
        if df.empty or len(df) < self.LOOKBACK_PERIOD:
            return

        long_entry_cond = df['close'] > df['rolling_high']
        short_entry_cond = df['close'] < df['rolling_low']

        df.loc[long_entry_cond, 'entry_signal'] = 'LONG'
        df.loc[long_entry_cond, 'stop_loss'] = df['rolling_high']
        risk_long = df['close'] - df['stop_loss']
        df.loc[long_entry_cond, 'target'] = df['close'] + (risk_long * self.TP_RR_RATIO)
        
        df.loc[short_entry_cond, 'entry_signal'] = 'SHORT'
        df.loc[short_entry_cond, 'stop_loss'] = df['rolling_low']
        risk_short = df['stop_loss'] - df['close']
        df.loc[short_entry_cond, 'target'] = df['close'] - (risk_short * self.TP_RR_RATIO)