# strategies/test_strategy.py

from strategies.base_strategy import BaseStrategy
import pandas as pd
import numpy as np
from typing import Optional # <-- Add this import

class TestStrategy(BaseStrategy):
    """
    Simple Test Strategy for the live trading engine.
    - Generates a LONG signal if close > open (bullish bar).
    - Generates a SHORT signal if close < open (bearish bar).
    - Uses a fixed 1% stop-loss and a 1:2 risk-reward ratio for the target.
    """
    def __init__(self, df: pd.DataFrame, symbol: Optional[str] = None, logger=None, primary_timeframe: int = 1, **kwargs): # <-- Change here
        super().__init__(df, symbol=symbol, logger=logger, primary_timeframe=primary_timeframe)
        self.name = "TestStrategy"
        self.primary_timeframe = primary_timeframe
        self.log(f"Initialized for {self.symbol} with {self.primary_timeframe}-min TF.")


    def calculate_indicators(self):
        """
        Copies the raw 1-minute data to the primary dataframe for processing.
        This ensures the strategy always uses the latest data provided by the engine.
        """
        if self.df_1min_raw.empty:
            self.df = pd.DataFrame()
            return
        # For a 1-min strategy, no resampling is needed. Just use the raw data.
        self.df = self.df_1min_raw.copy()

    def generate_signals(self):
        """
        Generates entry signals and calculates stop-loss and target levels.
        The main engine reads these columns from the last row of the DataFrame.
        """
        df = self.df
        if df.empty:
            return

        # Initialize columns that the main engine expects
        df['entry_signal'] = 'NONE'
        df['stop_loss'] = np.nan
        df['target'] = np.nan

        # Generate signals based on the last candle
        last_candle = df.iloc[-1]
        long_condition = last_candle['close'] > last_candle['open']
        short_condition = last_candle['close'] < last_candle['open']

        if long_condition:
            df.at[df.index[-1], 'entry_signal'] = 'LONG'
            stop_loss = last_candle['close'] * 0.99 # 1% SL
            risk = last_candle['close'] - stop_loss
            target = last_candle['close'] + (risk * 2) # 1:2 R:R
            df.at[df.index[-1], 'stop_loss'] = stop_loss
            df.at[df.index[-1], 'target'] = target

        elif short_condition:
            df.at[df.index[-1], 'entry_signal'] = 'SHORT'
            stop_loss = last_candle['close'] * 1.01 # 1% SL
            risk = stop_loss - last_candle['close']
            target = last_candle['close'] - (risk * 2) # 1:2 R:R
            df.at[df.index[-1], 'stop_loss'] = stop_loss
            df.at[df.index[-1], 'target'] = target

    # We do NOT override the run() method. We let BaseStrategy.run() handle it.
    # The get_trades() method is also not needed for the live engine.