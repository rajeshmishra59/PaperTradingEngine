# strategies/rangebound_strategy.py

import pandas as pd
import numpy as np
from ta.volatility import BollingerBands, AverageTrueRange
from ta.trend import ADXIndicator
from ta.momentum import StochasticOscillator
from typing import Optional
from strategies.base_strategy import BaseStrategy

class RangeBoundStrategy(BaseStrategy):
    """
    Intraday Range-Bound (Mean Reversion) Strategy for Nifty 50 stocks.
    - Plug-and-play with the existing paper trading engine.
    """
    def __init__(self, df: pd.DataFrame, symbol: Optional[str] = None, logger=None, primary_timeframe: int = 15, **kwargs):
        super().__init__(df, symbol=symbol, logger=logger, primary_timeframe=primary_timeframe)
        self.name = "RangeBoundStrategy"
        self.primary_timeframe = primary_timeframe
        self.sideways_state = {}  # {date: True/False}
        self.trade_count = {}     # {date: int}

    def calculate_indicators(self):
        if self.df_1min_raw.empty:
            self.df = pd.DataFrame()
            return

        df = self.df_1min_raw.copy()
        tf_string = f'{self.primary_timeframe}T'
        df_tf = df.resample(tf_string).agg({
            'open': 'first', 'high': 'max', 'low': 'min',
            'close': 'last', 'volume': 'sum'
        }).dropna().copy()

        # Bollinger Bands (20,2)
        bb = BollingerBands(df_tf['close'], window=20, window_dev=2)
        df_tf['bb_upper'] = bb.bollinger_hband()
        df_tf['bb_lower'] = bb.bollinger_lband()
        df_tf['bb_bandwidth'] = (df_tf['bb_upper'] - df_tf['bb_lower']) / df_tf['close'] * 100

        # ATR(14)
        df_tf['atr'] = AverageTrueRange(df_tf['high'], df_tf['low'], df_tf['close'], window=14).average_true_range()
        # ADX(14)
        df_tf['adx'] = ADXIndicator(df_tf['high'], df_tf['low'], df_tf['close'], window=14).adx()
        # Stochastic Oscillator (14,3,3)
        stoch = StochasticOscillator(df_tf['high'], df_tf['low'], df_tf['close'], window=14, smooth_window=3)
        df_tf['stoch_k'] = stoch.stoch()
        df_tf['stoch_d'] = stoch.stoch_signal()
        # VWAP (pandas style, not ta-lib)
        q = df_tf['volume']
        p = df_tf['close']
        df_tf['cum_vol'] = q.cumsum()
        df_tf['cum_vol_px'] = (q * p).cumsum()
        df_tf['vwap'] = df_tf['cum_vol_px'] / df_tf['cum_vol']
        df_tf['vol_avg'] = df_tf['volume'].rolling(20, min_periods=1).mean()
        df_tf['date'] = df_tf.index.date
        self.df = df_tf

    def generate_signals(self):
        df = self.df
        if df.empty or len(df) < 30:
            return

        df['entry_signal'] = 'NONE'
        df['stop_loss'] = np.nan
        df['target'] = np.nan
        df['trailing_sl_pct'] = np.nan

        now = df.index[-1]
        today = now.date()
        last = df.iloc[-1]
        prev = df.iloc[-2]
        price = last['close']

        # --- 1. Market Condition Filter (set per day after 10:30) ---
        after_1030 = now.time() >= pd.to_datetime("10:30").time()
        sideways = False
        if after_1030 and today not in self.sideways_state:
            bb_squeeze = last['bb_bandwidth'] <= 0.5
            adx_low = last['adx'] < 20
            # Horizontal range: price touched support/resistance 3+ times (quick/dirty way: use BB touches as proxy)
            touches_lower = (df['low'] <= df['bb_lower']).sum()
            touches_upper = (df['high'] >= df['bb_upper']).sum()
            sideways = bb_squeeze and adx_low and (touches_lower >= 3 and touches_upper >= 3)
            self.sideways_state[today] = sideways
        if today not in self.sideways_state:
            return  # Don't trade before 10:30, or not enough info
        if not self.sideways_state[today]:
            return  # Only trade if sideways detected

        # --- Trade frequency filter ---
        self.trade_count.setdefault(today, 0)
        if self.trade_count[today] >= 3:
            return  # Max 3 trades/day

        # --- Time filter ---
        if not (now.time() >= pd.to_datetime("10:30").time() and now.time() <= pd.to_datetime("14:00").time()):
            return

        # --- No trade on event days, expanding BB, or >1% from VWAP ---
        if last['bb_bandwidth'] > 1.0:
            return
        if abs(price - last['vwap']) / price > 0.01:
            return

        # --- Long Entry ---
        long_cond = (
            price <= last['bb_lower'] + 0.01*price and
            last['stoch_k'] <= 20 and
            (last['close'] > last['open']) and  # bullish reversal candle, can be made stricter
            last['volume'] > 1.5 * last['vol_avg'] and
            abs(price - last['vwap']) / price <= 0.005
        )
        # --- Short Entry ---
        short_cond = (
            price >= last['bb_upper'] - 0.01*price and
            last['stoch_k'] >= 80 and
            (last['close'] < last['open']) and  # bearish reversal candle, can be made stricter
            last['volume'] > 1.5 * last['vol_avg'] and
            abs(price - last['vwap']) / price <= 0.005
        )

        # --- Output columns (as per engine spec) ---
        if long_cond:
            atr_mult = 0.8
            if last['atr'] < 5: atr_mult = 0.5
            sl = price - (atr_mult * last['atr'])
            # Could use swing low as alternative, or the tighter of the two
            risk = price - sl
            tp3 = price + (3 * risk)
            df.at[df.index[-1], 'entry_signal'] = 'LONG'
            df.at[df.index[-1], 'stop_loss'] = sl
            df.at[df.index[-1], 'target'] = tp3
            df.at[df.index[-1], 'trailing_sl_pct'] = 0
            self.trade_count[today] += 1

        elif short_cond:
            atr_mult = 0.8
            if last['atr'] < 5: atr_mult = 0.5
            sl = price + (atr_mult * last['atr'])
            risk = sl - price
            tp3 = price - (3 * risk)
            df.at[df.index[-1], 'entry_signal'] = 'SHORT'
            df.at[df.index[-1], 'stop_loss'] = sl
            df.at[df.index[-1], 'target'] = tp3
            df.at[df.index[-1], 'trailing_sl_pct'] = 0
            self.trade_count[today] += 1

    # No override for run(), compatible with your live engine

