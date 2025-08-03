# File: numerouno_strategy.py (v4.1 - Final Corrected Version)
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import logging
from .base_strategy import BaseStrategy

class NumeroUnoStrategy(BaseStrategy):
    """
    NumeroUno Strategy with Trailing Stop-Loss support.
    """
    def __init__(self, df: pd.DataFrame, symbol: str = None, logger=None, primary_timeframe: int = 5,
                 pivot_lookback: int = 10, volume_ma_period: int = 20,
                 volume_spike_multiplier: float = 1.5, tp1_rr_ratio: float = 1.5,
                 tp2_rr_ratio: float = 3.0, pattern_confirmation_window: int = 60,
                 trailing_sl_pct: float = 0.5, **kwargs):

        super().__init__(df, symbol=symbol, logger=logger, primary_timeframe=primary_timeframe)
        self.name = "NumeroUno"
        # --- THIS LINE WAS MISSING IN THE PREVIOUS VERSION ---
        self.primary_timeframe = primary_timeframe
        # ----------------------------------------------------
        self.PIVOT_LOOKBACK, self.VOLUME_MA_PERIOD = pivot_lookback, volume_ma_period
        self.VOLUME_SPIKE_MULTIPLIER, self.TP1_RR_RATIO = volume_spike_multiplier, tp1_rr_ratio
        self.TP2_RR_RATIO, self.PATTERN_WINDOW = tp2_rr_ratio, pattern_confirmation_window
        self.TRAILING_SL_PCT = trailing_sl_pct
        
        self.log(f"NumeroUnoStrategy (v4.1) initialized for {self.symbol} with {self.primary_timeframe}-min timeframe.")

    def calculate_indicators(self):
        if self.df_1min_raw.empty: return
        tf_string = f'{self.primary_timeframe}T'
        self.df = self.df_1min_raw.resample(tf_string).agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
        if self.df.empty: return
        df = self.df
        high_peaks, _ = find_peaks(df['high'], distance=self.PIVOT_LOOKBACK)
        df['pivot_high'] = np.nan; df.iloc[high_peaks, df.columns.get_loc('pivot_high')] = df.iloc[high_peaks]['high']
        low_peaks, _ = find_peaks(-df['low'], distance=self.PIVOT_LOOKBACK)
        df['pivot_low'] = np.nan; df.iloc[low_peaks, df.columns.get_loc('pivot_low')] = df.iloc[low_peaks]['low']
        df['volume_avg'] = df['volume'].rolling(self.VOLUME_MA_PERIOD).mean()
        df['has_volume_spike'] = df['volume'] > (df['volume_avg'] * self.VOLUME_SPIKE_MULTIPLIER)

    def generate_signals(self):
        df = self.df
        df['entry_signal'], df['stop_loss'], df['tp1'], df['target'], df['trailing_sl_pct'] = 'NONE', np.nan, np.nan, np.nan, 0.0
        
        if 'pivot_high' not in df.columns or df.empty: return

        pivot_highs = df.dropna(subset=['pivot_high'])
        pivot_lows = df.dropna(subset=['pivot_low'])

        for i in range(1, len(pivot_lows)):
            b2_idx, b2_row = pivot_lows.index[i], pivot_lows.iloc[i]
            b1_idx, b1_row = pivot_lows.index[i-1], pivot_lows.iloc[i-1]
            if (b2_idx - b1_idx).total_seconds() / 60 > self.PATTERN_WINDOW: continue
            b1_price, b2_price = b1_row['pivot_low'], b2_row['pivot_low']
            if abs(b1_price - b2_price) / b1_price > 0.02: continue
            neckline_cands = pivot_highs[(pivot_highs.index > b1_idx) & (pivot_highs.index < b2_idx)]
            if neckline_cands.empty: continue
            neckline_price = neckline_cands['pivot_high'].max()
            
            breakout_window = df[df.index > b2_idx]
            for idx, row in breakout_window.iterrows():
                if row['close'] > neckline_price and row['has_volume_spike']:
                    if df.loc[idx, 'entry_signal'] == 'NONE':
                        df.loc[idx, 'entry_signal'] = 'LONG'
                        sl = min(b1_price, b2_price)
                        risk = row['close'] - sl
                        if risk > 0:
                            df.loc[idx, 'stop_loss'], df.loc[idx, 'tp1'], df.loc[idx, 'target'], df.loc[idx, 'trailing_sl_pct'] = sl, row['close'] + (risk * self.TP1_RR_RATIO), row['close'] + (risk * self.TP2_RR_RATIO), self.TRAILING_SL_PCT
                    break 

        for i in range(1, len(pivot_highs) - 1):
            ls_idx, ls_row = pivot_highs.index[i-1], pivot_highs.iloc[i-1]
            head_idx, head_row = pivot_highs.index[i], pivot_highs.iloc[i]
            rs_idx, rs_row = pivot_highs.index[i+1], pivot_highs.iloc[i+1]
            if (rs_idx - ls_idx).total_seconds() / 60 > self.PATTERN_WINDOW * 2: continue
            ls_price, head_price, rs_price = ls_row['pivot_high'], head_row['pivot_high'], rs_row['pivot_high']
            if head_price > ls_price and head_price > rs_price:
                neckline_cands = pivot_lows[(pivot_lows.index > ls_idx) & (pivot_lows.index < rs_idx)]
                if neckline_cands.empty: continue
                neckline_price = neckline_cands['pivot_low'].min()
                
                breakdown_window = df[df.index > rs_idx]
                for idx, row in breakdown_window.iterrows():
                    if row['close'] < neckline_price and row['has_volume_spike']:
                        if df.loc[idx, 'entry_signal'] == 'NONE':
                            df.loc[idx, 'entry_signal'] = 'SHORT'
                            sl = head_price
                            risk = sl - row['close']
                            if risk > 0:
                                df.loc[idx, 'stop_loss'], df.loc[idx, 'tp1'], df.loc[idx, 'target'], df.loc[idx, 'trailing_sl_pct'] = sl, row['close'] - (risk * self.TP1_RR_RATIO), row['close'] - (risk * self.TP2_RR_RATIO), self.TRAILING_SL_PCT
                        break