# File: apex_strategy.py (v3.1 - Final Corrected Version)
import pandas as pd
import numpy as np
import logging
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)
class ApexStrategy(BaseStrategy):
    """
    Apex Strategy (Triangle Breakout) with Trailing Stop-Loss support.
    """
    def __init__(self, df: pd.DataFrame, symbol: str = None, logger=None,
                 primary_timeframe: int = 5,
                 lookback_period: int = 10,
                 tp_rr_ratio: float = 2.0,
                 trailing_sl_pct: float = 0.5):

        super().__init__(df, symbol=symbol, logger=logger, primary_timeframe=primary_timeframe)
        self.name = "Apex"
        # --- THIS LINE WAS MISSING IN THE PREVIOUS VERSION ---
        self.primary_timeframe = primary_timeframe
        # ----------------------------------------------------
        self.LOOKBACK_PERIOD = lookback_period
        self.TP_RR_RATIO = tp_rr_ratio
        self.TRAILING_SL_PCT = trailing_sl_pct
        
        self.log(f"ApexStrategy (v3.1) initialized for {self.symbol} with {self.primary_timeframe} min TF.")

    def calculate_indicators(self):
        if self.df_1min_raw.empty:
            self.df = pd.DataFrame(); return

        tf_string = f'{self.primary_timeframe}T'
        self.df = self.df_1min_raw.resample(tf_string).agg(
            {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
        ).dropna()

        df = self.df
        if df.empty or len(df) < self.LOOKBACK_PERIOD: return

        df['rolling_high'] = df['high'].rolling(window=self.LOOKBACK_PERIOD).max().shift(1)
        df['rolling_low'] = df['low'].rolling(window=self.LOOKBACK_PERIOD).min().shift(1)
        
    def generate_signals(self):
        df = self.df
        df['entry_signal'], df['stop_loss'], df['target'], df['trailing_sl_pct'] = 'NONE', np.nan, np.nan, 0.0
        
        if df.empty or 'rolling_high' not in df.columns: return

        long_entry_cond = df['close'] > df['rolling_high']
        short_entry_cond = df['close'] < df['rolling_low']

        df.loc[long_entry_cond, 'entry_signal'] = 'LONG'
        df.loc[long_entry_cond, 'stop_loss'] = df['rolling_low'] 
        risk_long = df['close'] - df['stop_loss']
        df.loc[long_entry_cond, 'target'] = df['close'] + (risk_long * self.TP_RR_RATIO)
        
        df.loc[short_entry_cond, 'entry_signal'] = 'SHORT'
        df.loc[short_entry_cond, 'stop_loss'] = df['rolling_high']
        risk_short = df['stop_loss'] - df['close']
        df.loc[short_entry_cond, 'target'] = df['close'] - (risk_short * self.TP_RR_RATIO)

        active_signals = (df['entry_signal'] != 'NONE')
        df.loc[active_signals, 'trailing_sl_pct'] = self.TRAILING_SL_PCT