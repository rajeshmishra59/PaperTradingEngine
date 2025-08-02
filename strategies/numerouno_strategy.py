# File: strategies/numerouno_strategy.py
# Production Grade Version 2.0 - Final Patch

import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from .base_strategy import BaseStrategy

class NumeroUnoStrategy(BaseStrategy):
    """
    NumeroUno Strategy (v2.0): Trades based on W-Pattern and Head & Shoulders patterns.
    """
    def __init__(self, df: pd.DataFrame, symbol: str = None, logger=None, 
                 primary_timeframe: int = 5, **kwargs):

        super().__init__(df, symbol=symbol, logger=logger, primary_timeframe=primary_timeframe)
        self.name = "NumeroUno"
        
        # --- FIX: Yeh line jodna zaroori hai ---
        self.primary_timeframe = primary_timeframe
        
        # Strategy-specific parameters
        self.PIVOT_LOOKBACK = 10
        self.VOLUME_MA_PERIOD = 20
        self.VOLUME_SPIKE_MULTIPLIER = 1.5
        self.TP1_RR_RATIO = 1.5
        self.TP2_RR_RATIO = 3.0
        self.PATTERN_WINDOW = 60
        
        self.log(f"NumeroUnoStrategy (v2.0) initialized for {self.symbol} with {self.primary_timeframe}-min timeframe.")

    def calculate_indicators(self):
        """Resamples data and calculates pivots and volume indicators."""
        if self.df_1min_raw.empty:
            self.df = pd.DataFrame()
            return
        
        tf_string = f'{self.primary_timeframe}T'
        self.df = self.df_1min_raw.resample(tf_string).agg(
            {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
        ).dropna()
        
        if self.df.empty: return
        df = self.df

        high_peaks_indices, _ = find_peaks(df['high'], distance=self.PIVOT_LOOKBACK)
        df['pivot_high'] = np.nan
        df.iloc[high_peaks_indices, df.columns.get_loc('pivot_high')] = df.iloc[high_peaks_indices]['high']

        low_peaks_indices, _ = find_peaks(-df['low'], distance=self.PIVOT_LOOKBACK)
        df['pivot_low'] = np.nan
        df.iloc[low_peaks_indices, df.columns.get_loc('pivot_low')] = df.iloc[low_peaks_indices]['low']
        
        df['volume_avg'] = df['volume'].rolling(window=self.VOLUME_MA_PERIOD, min_periods=1).mean()
        df['has_volume_spike'] = df['volume'] > (df['volume_avg'] * self.VOLUME_SPIKE_MULTIPLIER)

    def generate_signals(self):
        """Identifies patterns and generates entry/exit signals."""
        df = self.df
        
        df['entry_signal'] = 'NONE'
        df['exit_signal'] = 'NONE' 
        df['stop_loss'] = np.nan
        df['tp1'] = np.nan
        df['target'] = np.nan
        
        if 'pivot_high' not in df.columns or df.empty:
            self.log("Indicators not calculated or DataFrame is empty.", level='warning')
            return

        pivot_highs = df.dropna(subset=['pivot_high'])
        pivot_lows = df.dropna(subset=['pivot_low'])

        # --- W-Pattern (Long) Logic ---
        for i in range(1, len(pivot_lows)):
            b2_idx, b2_row = pivot_lows.index[i], pivot_lows.iloc[i]
            b1_idx, b1_row = pivot_lows.index[i-1], pivot_lows.iloc[i-1]
            
            if (b2_idx - b1_idx).total_seconds() / 60 > self.PATTERN_WINDOW: continue
            if abs(b1_row['pivot_low'] - b2_row['pivot_low']) / b1_row['pivot_low'] > 0.02: continue

            neckline_cands = pivot_highs[(pivot_highs.index > b1_idx) & (pivot_highs.index < b2_idx)]
            if neckline_cands.empty: continue
            
            neckline_price = neckline_cands['pivot_high'].max()
            
            breakout_window = df[(df.index > b2_idx) & (df.index <= b2_idx + pd.Timedelta(minutes=self.primary_timeframe * 3))]
            for idx, row in breakout_window.iterrows():
                if row['close'] > neckline_price and row['has_volume_spike'] and df.loc[idx, 'entry_signal'] == 'NONE':
                    df.loc[idx, 'entry_signal'] = 'LONG'
                    sl = min(b1_row['pivot_low'], b2_row['pivot_low'])
                    risk = row['close'] - sl
                    if risk > 0:
                        df.loc[idx, 'stop_loss'] = sl
                        df.loc[idx, 'tp1'] = row['close'] + (risk * self.TP1_RR_RATIO)
                        df.loc[idx, 'target'] = row['close'] + (risk * self.TP2_RR_RATIO)
                    break 

        # --- Head & Shoulders (Short) Logic ---
        for i in range(1, len(pivot_highs) - 1):
            ls_idx, ls_row = pivot_highs.index[i-1], pivot_highs.iloc[i-1]
            head_idx, head_row = pivot_highs.index[i], pivot_highs.iloc[i]
            rs_idx, rs_row = pivot_highs.index[i+1], pivot_highs.iloc[i+1]
            
            if (rs_idx - ls_idx).total_seconds() / 60 > self.PATTERN_WINDOW * 2: continue
            if not (head_row['pivot_high'] > ls_row['pivot_high'] and head_row['pivot_high'] > rs_row['pivot_high']): continue

            neckline_cands = pivot_lows[(pivot_lows.index > ls_idx) & (pivot_lows.index < rs_idx)]
            if neckline_cands.empty: continue
            
            neckline_price = neckline_cands['pivot_low'].min()
            
            breakdown_window = df[(df.index > rs_idx) & (df.index <= rs_idx + pd.Timedelta(minutes=self.primary_timeframe * 3))]
            for idx, row in breakdown_window.iterrows():
                if row['close'] < neckline_price and row['has_volume_spike'] and df.loc[idx, 'entry_signal'] == 'NONE':
                    df.loc[idx, 'entry_signal'] = 'SHORT'
                    sl = head_row['pivot_high']
                    risk = sl - row['close']
                    if risk > 0:
                        df.loc[idx, 'stop_loss'] = sl
                        df.loc[idx, 'tp1'] = row['close'] - (risk * self.TP1_RR_RATIO)
                        df.loc[idx, 'target'] = row['close'] - (risk * self.TP2_RR_RATIO)
                    break