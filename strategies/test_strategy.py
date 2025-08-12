# strategies/test_strategy.py

from strategies.base_strategy import BaseStrategy
import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, ADXIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from typing import Optional

class TestStrategy(BaseStrategy):
    """
    Intraday Trending Market Strategy for Nifty 50 (15-min).
    - EMA9, EMA21, ATR14, RSI14, ADX14, 150% volume spike.
    - Entry only if trend confirmed, retracement, reversal candle & volume spike.
    - Fully compatible with live engine requirements.
    """
    def __init__(self, df: pd.DataFrame, symbol: Optional[str] = None, logger=None, primary_timeframe: int = 15, **kwargs):
        super().__init__(df, symbol=symbol, logger=logger, primary_timeframe=primary_timeframe)
        self.name = "TestStrategy"
        self.primary_timeframe = primary_timeframe
        self.trend_state = {}  # {date: 'BULLISH'/'BEARISH'/None}
        self.log(f"Initialized for {self.symbol} with {self.primary_timeframe}-min TF.")

    def calculate_indicators(self):
        if self.df_1min_raw.empty:
            self.df = pd.DataFrame()
            return
        df = self.df_1min_raw.copy()
        # Use 15-min resample for indicators and trading logic
        df_15 = df.resample('15T').agg({
            'open': 'first', 'high': 'max', 'low': 'min',
            'close': 'last', 'volume': 'sum'
        }).dropna().copy()
        df_15['ema9'] = EMAIndicator(df_15['close'], window=9).ema_indicator()
        df_15['ema21'] = EMAIndicator(df_15['close'], window=21).ema_indicator()
        df_15['atr'] = AverageTrueRange(df_15['high'], df_15['low'], df_15['close'], window=14).average_true_range()
        df_15['rsi'] = RSIIndicator(df_15['close'], window=14).rsi()
        df_15['adx'] = ADXIndicator(df_15['high'], df_15['low'], df_15['close'], window=14).adx()
        df_15['vol_avg'] = df_15['volume'].rolling(20, min_periods=1).mean()
        df_15['date'] = df_15.index.date
        self.df = df_15

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
        adx, rsi, atr = last['adx'], last['rsi'], last['atr']
        ema9, ema21, price, volume, vol_avg = last['ema9'], last['ema21'], last['close'], last['volume'], last['vol_avg']

        # 1. PRE-9:30AM Trend Detection (store per day)
        pre930 = df.between_time("09:15", "09:30")
        if today not in self.trend_state:
            trend = None
            if not pre930.empty and pre930['adx'].iloc[-1] >= 25:
                if pre930['ema9'].iloc[-1] > pre930['ema21'].iloc[-1] and pre930['close'].iloc[-1] > pre930['ema21'].iloc[-1]:
                    trend = "BULLISH"
                elif pre930['ema9'].iloc[-1] < pre930['ema21'].iloc[-1] and pre930['close'].iloc[-1] < pre930['ema21'].iloc[-1]:
                    trend = "BEARISH"
            self.trend_state[today] = trend

        today_trend = self.trend_state.get(today, None)
        if today_trend is None or adx < 25 or atr < 15:
            return

        if not (now.time() >= pd.to_datetime("09:30").time() and now.time() < pd.to_datetime("15:00").time()):
            return

        # Entry logic: only fire signal on last candle if all rules match

        # BULLISH SCENARIO
        if today_trend == "BULLISH":
            rsi_ok = 40 <= rsi <= 45
            price_near_ema9 = abs(price - ema9) <= 0.10 * atr
            bullish_candle = (last['close'] > last['open']) and (last['low'] <= ema9 <= last['close'])
            bullish_engulfing = (last['close'] > last['open']) and (prev['close'] < prev['open']) and (last['close'] > prev['open'])
            vol_ok = volume > 1.5 * vol_avg
            if rsi_ok and price_near_ema9 and (bullish_candle or bullish_engulfing) and vol_ok:
                atr_mult = 1.5
                if atr < 20: atr_mult = 1.25
                if atr > 50: atr_mult = 2
                sl = price - (atr_mult * atr)
                risk = price - sl
                tp2 = price + (4 * risk)
                df.at[df.index[-1], 'entry_signal'] = 'LONG'
                df.at[df.index[-1], 'stop_loss'] = sl
                df.at[df.index[-1], 'target'] = tp2
                df.at[df.index[-1], 'trailing_sl_pct'] = 0

        # BEARISH SCENARIO
        if today_trend == "BEARISH":
            rsi_ok = 55 <= rsi <= 60
            price_near_ema9 = abs(price - ema9) <= 0.10 * atr
            bearish_candle = (last['close'] < last['open']) and (last['high'] >= ema9 >= last['close'])
            bearish_engulfing = (last['close'] < last['open']) and (prev['close'] > prev['open']) and (last['close'] < prev['open'])
            vol_ok = volume > 1.5 * vol_avg
            if rsi_ok and price_near_ema9 and (bearish_candle or bearish_engulfing) and vol_ok:
                atr_mult = 1.5
                if atr < 20: atr_mult = 1.25
                if atr > 50: atr_mult = 2
                sl = price + (atr_mult * atr)
                risk = sl - price
                tp2 = price - (4 * risk)
                df.at[df.index[-1], 'entry_signal'] = 'SHORT'
                df.at[df.index[-1], 'stop_loss'] = sl
                df.at[df.index[-1], 'target'] = tp2
                df.at[df.index[-1], 'trailing_sl_pct'] = 0

    # Do NOT override run(); engine calls calculate_indicators/generate_signals in order

