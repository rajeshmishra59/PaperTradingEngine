# File: apex_strategy.py (Final Corrected Version)
import pandas as pd
import numpy as np
import logging
from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)
class ApexStrategy(BaseStrategy):
    def __init__(self, df: pd.DataFrame, symbol: str = None, logger=None,
                 primary_timeframe: int = 5,
                 lookback_period: int = 10,
                 tp_rr_ratio: float = 2.0,
                 trailing_sl_pct: float = 0.5):

        super().__init__(df, symbol=symbol, logger=logger, primary_timeframe=primary_timeframe)
        self.name = "Apex"
        self.primary_timeframe = primary_timeframe
        self.LOOKBACK_PERIOD = lookback_period
        self.TP_RR_RATIO = tp_rr_ratio
        self.TRAILING_SL_PCT = trailing_sl_pct
        self.log(f"ApexStrategy initialized for {self.symbol} with {self.primary_timeframe} min TF.")

    def calculate_indicators(self):
        if self.df_1min_raw.empty: self.df = pd.DataFrame(); return
        tf_string = f'{self.primary_timeframe}T'
        self.df = self.df_1min_raw.resample(tf_string).agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
        if self.df.empty or len(self.df) < self.LOOKBACK_PERIOD: return
        self.df['rolling_high'] = self.df['high'].rolling(window=self.LOOKBACK_PERIOD).max().shift(1)
        self.df['rolling_low'] = self.df['low'].rolling(window=self.LOOKBACK_PERIOD).min().shift(1)
        
    def generate_signals(self):
        df = self.df
        df['entry_signal'], df['stop_loss'], df['target'], df['trailing_sl_pct'] = 'NONE', np.nan, np.nan, 0.0
        if df.empty or 'rolling_high' not in df.columns: return
        long_entry = df['close'] > df['rolling_high']
        short_entry = df['close'] < df['rolling_low']
        df.loc[long_entry, 'entry_signal'] = 'LONG'
        df.loc[long_entry, 'stop_loss'] = df['rolling_low'] 
        risk_long = df['close'] - df['stop_loss']
        df.loc[long_entry, 'target'] = df['close'] + (risk_long * self.TP_RR_RATIO)
        df.loc[short_entry, 'entry_signal'] = 'SHORT'
        df.loc[short_entry, 'stop_loss'] = df['rolling_high']
        risk_short = df['stop_loss'] - df['close']
        df.loc[short_entry, 'target'] = df['close'] - (risk_short * self.TP_RR_RATIO)
        df.loc[(long_entry | short_entry), 'trailing_sl_pct'] = self.TRAILING_SL_PCT