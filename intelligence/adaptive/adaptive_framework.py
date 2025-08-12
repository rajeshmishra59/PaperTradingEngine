"""
ADAPTIVE MULTI-STRATEGY FRAMEWORK
Advanced Trading System with Market Regime Detection and Multi-Timeframe Analysis
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import talib

class MarketRegime(Enum):
    """Market Regime Types"""
    TRENDING_BULLISH = "trending_bullish"
    TRENDING_BEARISH = "trending_bearish"
    RANGE_BOUND = "range_bound"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"

@dataclass
class MarketCondition:
    """Market Condition Data Structure"""
    regime: MarketRegime
    volatility_percentile: float
    trend_strength: float
    momentum: float
    volume_profile: str
    confidence: float

class RegimeDetector:
    """Advanced Market Regime Detection System"""
    
    def __init__(self, lookback_period: int = 50):
        self.lookback_period = lookback_period
        
    def detect_regime(self, data: pd.DataFrame) -> MarketCondition:
        """
        Comprehensive Market Regime Detection
        Uses multiple indicators to determine market state
        """
        # 1. Volatility Analysis
        volatility = self._calculate_volatility_regime(data)
        
        # 2. Trend Analysis
        trend_data = self._analyze_trend_strength(data)
        
        # 3. Range Analysis
        range_data = self._detect_range_bound(data)
        
        # 4. Volume Profile
        volume_profile = self._analyze_volume_profile(data)
        
        # 5. Momentum Analysis
        momentum = self._calculate_momentum(data)
        
        # Combine all factors to determine regime
        regime = self._determine_primary_regime(
            volatility, trend_data, range_data, momentum
        )
        
        return MarketCondition(
            regime=regime,
            volatility_percentile=volatility['percentile'],
            trend_strength=trend_data['strength'],
            momentum=momentum,
            volume_profile=volume_profile,
            confidence=self._calculate_confidence(volatility, trend_data, range_data)
        )
    
    def _calculate_volatility_regime(self, data: pd.DataFrame) -> Dict:
        """ATR-based volatility analysis"""
        atr = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)
        atr_ma = atr.rolling(self.lookback_period).mean()
        current_atr = atr.iloc[-1]
        atr_percentile = (atr.rank(pct=True).iloc[-1]) * 100
        
        return {
            'current': current_atr,
            'average': atr_ma.iloc[-1],
            'percentile': atr_percentile,
            'is_high': atr_percentile > 70,
            'is_low': atr_percentile < 30
        }
    
    def _analyze_trend_strength(self, data: pd.DataFrame) -> Dict:
        """Multi-timeframe trend analysis"""
        close = data['close']
        
        # ADX for trend strength
        adx = talib.ADX(data['high'], data['low'], data['close'], timeperiod=14)
        
        # Moving average alignment
        ma_20 = talib.SMA(close, timeperiod=20)
        ma_50 = talib.SMA(close, timeperiod=50)
        
        # Price vs MA position
        price_vs_ma = close.iloc[-1] / ma_20.iloc[-1]
        ma_alignment = ma_20.iloc[-1] > ma_50.iloc[-1]
        
        trend_strength = adx.iloc[-1] if not np.isnan(adx.iloc[-1]) else 0
        
        return {
            'strength': trend_strength,
            'direction': 'bullish' if price_vs_ma > 1.01 and ma_alignment else 'bearish' if price_vs_ma < 0.99 and not ma_alignment else 'neutral',
            'is_strong': trend_strength > 25,
            'ma_alignment': ma_alignment
        }
    
    def _detect_range_bound(self, data: pd.DataFrame) -> Dict:
        """Range-bound market detection"""
        close = data['close']
        high = data['high']
        low = data['low']
        
        # Bollinger Bands for range detection
        bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=20)
        bb_width = (bb_upper - bb_lower) / bb_middle
        
        # Price channel analysis
        highest_high = high.rolling(self.lookback_period).max()
        lowest_low = low.rolling(self.lookback_period).min()
        range_width = (highest_high - lowest_low) / close
        
        current_bb_width = bb_width.iloc[-1]
        avg_bb_width = bb_width.rolling(self.lookback_period).mean().iloc[-1]
        
        return {
            'bb_width': current_bb_width,
            'bb_width_percentile': (bb_width.rank(pct=True).iloc[-1]) * 100,
            'is_range_bound': current_bb_width < avg_bb_width * 0.8,
            'range_width': range_width.iloc[-1]
        }
    
    def _analyze_volume_profile(self, data: pd.DataFrame) -> str:
        """Volume analysis"""
        volume = data['volume']
        avg_volume = volume.rolling(20).mean()
        
        current_vol_ratio = volume.iloc[-1] / avg_volume.iloc[-1]
        
        if current_vol_ratio > 1.5:
            return "high_volume"
        elif current_vol_ratio < 0.7:
            return "low_volume"
        else:
            return "normal_volume"
    
    def _calculate_momentum(self, data: pd.DataFrame) -> float:
        """RSI-based momentum calculation"""
        rsi = talib.RSI(data['close'], timeperiod=14)
        return rsi.iloc[-1] if not np.isnan(rsi.iloc[-1]) else 50
    
    def _determine_primary_regime(self, volatility, trend_data, range_data, momentum) -> MarketRegime:
        """Logic to determine primary market regime"""
        
        # High volatility breakout
        if volatility['is_high'] and trend_data['is_strong']:
            if trend_data['direction'] == 'bullish':
                return MarketRegime.TRENDING_BULLISH
            else:
                return MarketRegime.TRENDING_BEARISH
        
        # Range-bound conditions
        elif range_data['is_range_bound'] and not trend_data['is_strong']:
            return MarketRegime.RANGE_BOUND
        
        # Volatility-based regimes
        elif volatility['is_high']:
            return MarketRegime.HIGH_VOLATILITY
        elif volatility['is_low']:
            return MarketRegime.LOW_VOLATILITY
        
        # Default to trend analysis
        else:
            if trend_data['direction'] == 'bullish':
                return MarketRegime.TRENDING_BULLISH
            elif trend_data['direction'] == 'bearish':
                return MarketRegime.TRENDING_BEARISH
            else:
                return MarketRegime.RANGE_BOUND
    
    def _calculate_confidence(self, volatility, trend_data, range_data) -> float:
        """Calculate confidence in regime detection"""
        factors = []
        
        # Volatility clarity
        if volatility['percentile'] > 80 or volatility['percentile'] < 20:
            factors.append(0.3)
        
        # Trend clarity
        if trend_data['strength'] > 30:
            factors.append(0.4)
        
        # Range clarity
        if range_data['bb_width_percentile'] < 25:
            factors.append(0.3)
        
        return sum(factors)

class AdaptiveIndicators:
    """Dynamic indicator parameters based on market conditions"""
    
    @staticmethod
    def adaptive_atr_stops(data: pd.DataFrame, base_multiplier: float = 2.0) -> Tuple[float, float]:
        """ATR-based adaptive stop loss and targets"""
        atr = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)
        current_atr = atr.iloc[-1]
        close = data['close'].iloc[-1]
        
        # Adaptive multiplier based on volatility percentile
        atr_percentile = (atr.rank(pct=True).iloc[-1]) * 100
        
        if atr_percentile > 80:  # High volatility
            multiplier = base_multiplier * 1.5
        elif atr_percentile < 20:  # Low volatility
            multiplier = base_multiplier * 0.7
        else:
            multiplier = base_multiplier
        
        stop_distance = current_atr * multiplier
        target_distance = current_atr * multiplier * 2  # 2:1 RR
        
        return stop_distance, target_distance
    
    @staticmethod
    def adaptive_bollinger_bands(data: pd.DataFrame, market_condition: MarketCondition) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Adaptive Bollinger Bands based on market regime"""
        close = data['close']
        
        # Adjust period and std dev based on regime
        if market_condition.regime in [MarketRegime.HIGH_VOLATILITY, MarketRegime.BREAKOUT]:
            period = 10  # Shorter period for volatile markets
            std_dev = 2.5  # Wider bands
        elif market_condition.regime == MarketRegime.RANGE_BOUND:
            period = 20  # Standard period
            std_dev = 1.8  # Tighter bands for range trading
        else:
            period = 20  # Standard
            std_dev = 2.0  # Standard
        
        return talib.BBANDS(close, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev)
    
    @staticmethod
    def adaptive_rsi(data: pd.DataFrame, market_condition: MarketCondition) -> pd.Series:
        """Adaptive RSI parameters"""
        close = data['close']
        
        # Adjust RSI period based on market regime
        if market_condition.regime in [MarketRegime.HIGH_VOLATILITY, MarketRegime.BREAKOUT]:
            period = 7  # Faster RSI for volatile markets
        elif market_condition.regime == MarketRegime.RANGE_BOUND:
            period = 21  # Slower RSI for range-bound markets
        else:
            period = 14  # Standard
        
        return talib.RSI(close, timeperiod=period)

class MultiTimeframeAnalysis:
    """Multi-timeframe confirmation system"""
    
    def __init__(self, primary_tf: str = '5m', confirmation_tf: str = '15m'):
        self.primary_tf = primary_tf
        self.confirmation_tf = confirmation_tf
    
    def get_higher_tf_bias(self, higher_tf_data: pd.DataFrame) -> Dict:
        """Get bias from higher timeframe"""
        close = higher_tf_data['close']
        
        # Trend analysis on higher TF
        ma_20 = talib.SMA(close, timeperiod=20)
        ma_50 = talib.SMA(close, timeperiod=50)
        
        # Current price position
        current_price = close.iloc[-1]
        ma_20_current = ma_20.iloc[-1]
        ma_50_current = ma_50.iloc[-1]
        
        # Determine bias
        if current_price > ma_20_current > ma_50_current:
            bias = "bullish"
            strength = (current_price - ma_20_current) / ma_20_current
        elif current_price < ma_20_current < ma_50_current:
            bias = "bearish"
            strength = (ma_20_current - current_price) / ma_20_current
        else:
            bias = "neutral"
            strength = 0
        
        return {
            'bias': bias,
            'strength': abs(strength),
            'ma_alignment': ma_20_current > ma_50_current,
            'price_vs_ma20': current_price / ma_20_current,
            'confirmation': strength > 0.01  # At least 1% away from MA
        }
    
    def confirm_entry(self, primary_signal: str, higher_tf_bias: Dict) -> bool:
        """Confirm entry based on multi-timeframe analysis"""
        if not higher_tf_bias['confirmation']:
            return False
        
        if primary_signal == 'buy' and higher_tf_bias['bias'] == 'bullish':
            return True
        elif primary_signal == 'sell' and higher_tf_bias['bias'] == 'bearish':
            return True
        
        return False

if __name__ == "__main__":
    print("🚀 ADAPTIVE MULTI-STRATEGY FRAMEWORK")
    print("✅ Market Regime Detection")
    print("✅ Adaptive Indicators") 
    print("✅ Multi-Timeframe Analysis")
    print("✅ Dynamic Parameter Adjustment")
    print("\nNext: Implement in existing strategies...")
