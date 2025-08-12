# File: strategies/sankhyaek_strategy.py (Final Guaranteed Code)

import pandas as pd
import numpy as np  # <-- यह लाइन 'from numpy import NaN' नहीं होनी चाहिए
import pandas_ta as ta
from datetime import time
from typing import Optional
from .base_strategy import BaseStrategy

class SankhyaEkStrategy(BaseStrategy):
    def __init__(self, df: pd.DataFrame, symbol: Optional[str] = None, logger=None, 
                 primary_timeframe: int = 5, **kwargs):

        super().__init__(df, symbol=symbol, logger=logger, primary_timeframe=primary_timeframe)
        self.name = "SankhyaEkStrategy"
        self.bb_length, self.bb_std, self.rsi_period = 20, 2.0, 14
        self.rsi_oversold, self.rsi_overbought = 30, 70
        self.stop_loss_pct, self.risk_reward_ratio = 0.01, 2.0
        self.max_trades_per_day, self.last_trade_date, self.signals_today = 3, None, 0
        self.trade_stop_time = time(14, 45)
        self.log(f"Initialized for {self.symbol} with {self.primary_timeframe}-min TF.")

    def calculate_indicators(self):
        if self.df_1min_raw.empty:
            self.log("Raw 1-minute data is empty.", level='warning')
            return

        tf_string = f'{self.primary_timeframe}T'
        resampled_df = self.df_1min_raw.resample(tf_string).agg(
            {'open':'first', 'high':'max', 'low':'min', 'close':'last', 'volume':'sum'}
        ).dropna()

        if len(resampled_df) < self.bb_length:
            self.log(f"Not enough data for indicators (need {self.bb_length}, have {len(resampled_df)}).", level='warning')
            return
            
        resampled_df.ta.bbands(length=self.bb_length, std=self.bb_std, append=True)
        resampled_df.ta.rsi(length=self.rsi_period, append=True)
        
        # Find the actual column names that contain our indicators
        bb_lower_col = next((col for col in resampled_df.columns if f'BBL_{self.bb_length}_' in col), None)
        bb_upper_col = next((col for col in resampled_df.columns if f'BBU_{self.bb_length}_' in col), None)
        rsi_col = next((col for col in resampled_df.columns if f'RSI_{self.rsi_period}' in col), None)
        
        # Build a renaming dictionary with only the columns that exist
        rename_dict = {}
        if bb_lower_col: rename_dict[bb_lower_col] = 'bb_lower'
        if bb_upper_col: rename_dict[bb_upper_col] = 'bb_upper'
        if rsi_col: rename_dict[rsi_col] = 'rsi'
        
        # Only rename if we found matches
        if rename_dict:
            resampled_df.rename(columns=rename_dict, inplace=True)
        
        # Debug info if needed columns are missing
        if not all(col in resampled_df.columns for col in ['bb_lower', 'bb_upper', 'rsi']):
            self.log("Indicator columns missing after rename. Found columns: " + 
                     ", ".join(sorted(c for c in resampled_df.columns if 'BB' in c or 'RSI' in c)), 
                     level='error')
            return
        self.df = resampled_df

    def generate_signals(self):
        if self.df.empty: return

        df = self.df
        df['entry_signal'], df['stop_loss'], df['target'] = 'NONE', np.nan, np.nan # <-- यहाँ np.nan का उपयोग
        
        latest_timestamp = df.index[-1]
        current_date, current_time = latest_timestamp.date(), latest_timestamp.time()

        if self.last_trade_date != current_date:
            self.log(f"New trading day: {current_date}. Resetting counter.")
            self.signals_today, self.last_trade_date = 0, current_date

        if self.signals_today >= self.max_trades_per_day or current_time >= self.trade_stop_time:
            return

        candle = df.iloc[-1]
        close, rsi = candle['close'], candle['rsi']
        bb_lower, bb_upper = candle['bb_lower'], candle['bb_upper']

        if (close < bb_lower) and (rsi < self.rsi_oversold):
            sl = close * (1 - self.stop_loss_pct)
            target = close + ((close - sl) * self.risk_reward_ratio)
            df.loc[df.index[-1], ['entry_signal', 'stop_loss', 'target']] = ['LONG', sl, target]
            self.signals_today += 1
            self.log(f"LONG signal! SL:{sl:.2f}, TGT:{target:.2f} ({self.signals_today}/{self.max_trades_per_day})", level='warning')
            return

        if (close > bb_upper) and (rsi > self.rsi_overbought):
            sl = close * (1 + self.stop_loss_pct)
            target = close - ((sl - close) * self.risk_reward_ratio)
            df.loc[df.index[-1], ['entry_signal', 'stop_loss', 'target']] = ['SHORT', sl, target]
            self.signals_today += 1
            self.log(f"SHORT signal! SL:{sl:.2f}, TGT:{target:.2f} ({self.signals_today}/{self.max_trades_per_day})", level='warning')