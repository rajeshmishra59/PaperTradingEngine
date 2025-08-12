"""
ENHANCED ADAPTIVE STRATEGY - AlphaOne with Multi-Regime Support
Implements all advanced concepts: regime detection, multi-TF, adaptive indicators
"""

import pandas as pd
import numpy as np
import talib
from typing import Dict, List, Tuple, Optional
from adaptive_framework import RegimeDetector, MarketCondition, MarketRegime, AdaptiveIndicators, MultiTimeframeAnalysis

class AdaptiveAlphaOneStrategy:
    """
    Enhanced AlphaOne Strategy with:
    1. Market Regime Detection
    2. Multi-Timeframe Confirmation
    3. Adaptive Indicators
    4. Dynamic Risk Management
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.regime_detector = RegimeDetector(lookback_period=50)
        self.mtf_analyzer = MultiTimeframeAnalysis(primary_tf='5m', confirmation_tf='15m')
        self.adaptive_indicators = AdaptiveIndicators()
        
        # Strategy state
        self.current_regime = None
        self.active_strategy_mode = None
        self.risk_multiplier = 1.0
        
        # Performance tracking
        self.regime_performance = {regime: {'wins': 0, 'losses': 0, 'pnl': 0} for regime in MarketRegime}
    
    def analyze_market_condition(self, data: pd.DataFrame, higher_tf_data: pd.DataFrame = None) -> MarketCondition:
        """Comprehensive market analysis"""
        # Detect current market regime
        market_condition = self.regime_detector.detect_regime(data)
        self.current_regime = market_condition.regime
        
        # Get higher timeframe bias if available
        if higher_tf_data is not None:
            htf_bias = self.mtf_analyzer.get_higher_tf_bias(higher_tf_data)
            market_condition.htf_bias = htf_bias
        
        return market_condition
    
    def select_strategy_mode(self, market_condition: MarketCondition) -> str:
        """Select appropriate strategy based on market regime"""
        regime = market_condition.regime
        
        if regime in [MarketRegime.TRENDING_BULLISH, MarketRegime.TRENDING_BEARISH]:
            return "trend_following"
        elif regime == MarketRegime.RANGE_BOUND:
            return "mean_reversion"
        elif regime == MarketRegime.HIGH_VOLATILITY:
            return "breakout_scalping"
        elif regime == MarketRegime.LOW_VOLATILITY:
            return "narrow_range_breakout"
        else:
            return "conservative"  # Default safe mode
    
    def trend_following_signals(self, data: pd.DataFrame, market_condition: MarketCondition) -> Dict:
        """Trend following strategy for trending markets"""
        close = data['close']
        high = data['high']
        low = data['low']
        
        # Adaptive moving averages
        if market_condition.volatility_percentile > 70:
            fast_period, slow_period = 8, 21  # Faster in volatile markets
        else:
            fast_period, slow_period = 12, 26  # Standard
        
        ma_fast = talib.SMA(close, timeperiod=fast_period)
        ma_slow = talib.SMA(close, timeperiod=slow_period)
        
        # MACD for momentum confirmation
        macd, macd_signal, macd_hist = talib.MACD(close)
        
        # ADX for trend strength
        adx = talib.ADX(high, low, close, timeperiod=14)
        
        # Adaptive Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.adaptive_indicators.adaptive_bollinger_bands(data, market_condition)
        
        # Entry conditions
        buy_signal = (
            (ma_fast.iloc[-1] > ma_slow.iloc[-1]) and  # MA crossover
            (ma_fast.iloc[-2] <= ma_slow.iloc[-2]) and  # Fresh crossover
            (adx.iloc[-1] > 25) and  # Strong trend
            (macd.iloc[-1] > macd_signal.iloc[-1]) and  # MACD confirmation
            (close.iloc[-1] > bb_middle.iloc[-1])  # Above middle BB
        )
        
        sell_signal = (
            (ma_fast.iloc[-1] < ma_slow.iloc[-1]) and
            (ma_fast.iloc[-2] >= ma_slow.iloc[-2]) and
            (adx.iloc[-1] > 25) and
            (macd.iloc[-1] < macd_signal.iloc[-1]) and
            (close.iloc[-1] < bb_middle.iloc[-1])
        )
        
        return {
            'buy': buy_signal,
            'sell': sell_signal,
            'strength': adx.iloc[-1] if not np.isnan(adx.iloc[-1]) else 0,
            'confidence': market_condition.confidence
        }
    
    def mean_reversion_signals(self, data: pd.DataFrame, market_condition: MarketCondition) -> Dict:
        """Mean reversion strategy for range-bound markets"""
        close = data['close']
        high = data['high']
        low = data['low']
        
        # Adaptive RSI
        rsi = self.adaptive_indicators.adaptive_rsi(data, market_condition)
        
        # Bollinger Bands for range trading
        bb_upper, bb_middle, bb_lower = self.adaptive_indicators.adaptive_bollinger_bands(data, market_condition)
        
        # Stochastic for oversold/overbought
        stoch_k, stoch_d = talib.STOCH(high, low, close)
        
        # VWAP for mean reversion
        vwap = (close * data['volume']).cumsum() / data['volume'].cumsum()
        
        # Entry conditions for mean reversion
        buy_signal = (
            (rsi.iloc[-1] < 30) and  # Oversold
            (close.iloc[-1] < bb_lower.iloc[-1]) and  # Below lower BB
            (stoch_k.iloc[-1] < 20) and  # Stochastic oversold
            (close.iloc[-1] < vwap.iloc[-1] * 0.998)  # Below VWAP
        )
        
        sell_signal = (
            (rsi.iloc[-1] > 70) and  # Overbought
            (close.iloc[-1] > bb_upper.iloc[-1]) and  # Above upper BB
            (stoch_k.iloc[-1] > 80) and  # Stochastic overbought
            (close.iloc[-1] > vwap.iloc[-1] * 1.002)  # Above VWAP
        )
        
        return {
            'buy': buy_signal,
            'sell': sell_signal,
            'strength': abs(50 - rsi.iloc[-1]),  # Distance from neutral
            'confidence': market_condition.confidence
        }
    
    def breakout_scalping_signals(self, data: pd.DataFrame, market_condition: MarketCondition) -> Dict:
        """Breakout scalping for high volatility markets"""
        close = data['close']
        high = data['high']
        low = data['low']
        volume = data['volume']
        
        # Dynamic lookback based on volatility
        lookback = 10 if market_condition.volatility_percentile > 80 else 20
        
        # Support/Resistance levels
        resistance = high.rolling(lookback).max()
        support = low.rolling(lookback).min()
        
        # Volume confirmation
        avg_volume = volume.rolling(20).mean()
        volume_spike = volume.iloc[-1] > avg_volume.iloc[-1] * 1.5
        
        # ATR for volatility
        atr = talib.ATR(high, low, close, timeperiod=14)
        
        # Breakout conditions
        buy_signal = (
            (close.iloc[-1] > resistance.iloc[-2]) and  # Break above resistance
            (volume_spike) and  # Volume confirmation
            (atr.iloc[-1] > atr.rolling(20).mean().iloc[-1])  # Above average volatility
        )
        
        sell_signal = (
            (close.iloc[-1] < support.iloc[-2]) and  # Break below support
            (volume_spike) and
            (atr.iloc[-1] > atr.rolling(20).mean().iloc[-1])
        )
        
        return {
            'buy': buy_signal,
            'sell': sell_signal,
            'strength': atr.iloc[-1] / close.iloc[-1] * 100,  # Volatility as strength
            'confidence': market_condition.confidence
        }
    
    def get_adaptive_risk_params(self, data: pd.DataFrame, market_condition: MarketCondition, signal_strength: float) -> Dict:
        """Calculate adaptive risk management parameters"""
        # Base ATR stops
        stop_distance, target_distance = self.adaptive_indicators.adaptive_atr_stops(data)
        
        # Adjust based on regime
        regime_multipliers = {
            MarketRegime.TRENDING_BULLISH: 1.0,
            MarketRegime.TRENDING_BEARISH: 1.0,
            MarketRegime.RANGE_BOUND: 0.7,  # Tighter stops in ranges
            MarketRegime.HIGH_VOLATILITY: 1.5,  # Wider stops in volatile markets
            MarketRegime.LOW_VOLATILITY: 0.8,
            MarketRegime.BREAKOUT: 1.2
        }
        
        multiplier = regime_multipliers.get(market_condition.regime, 1.0)
        
        # Adjust based on confidence
        confidence_multiplier = 0.7 + (market_condition.confidence * 0.6)  # 0.7 to 1.3 range
        
        # Final adjustments
        final_stop = stop_distance * multiplier * confidence_multiplier
        final_target = target_distance * multiplier * confidence_multiplier
        
        # Position sizing based on volatility and confidence
        base_position_size = 1.0
        volatility_adjustment = 1.0 / (1.0 + market_condition.volatility_percentile / 100)
        confidence_adjustment = 0.5 + (market_condition.confidence * 0.5)
        
        position_size = base_position_size * volatility_adjustment * confidence_adjustment
        
        return {
            'stop_loss': final_stop,
            'target': final_target,
            'position_size': min(position_size, 1.5),  # Cap at 1.5x
            'risk_reward_ratio': final_target / final_stop
        }
    
    def generate_signals(self, data: pd.DataFrame, higher_tf_data: pd.DataFrame = None) -> Dict:
        """Main signal generation with adaptive logic"""
        # Analyze market condition
        market_condition = self.analyze_market_condition(data, higher_tf_data)
        
        # Select strategy mode
        strategy_mode = self.select_strategy_mode(market_condition)
        self.active_strategy_mode = strategy_mode
        
        # Generate signals based on strategy mode
        if strategy_mode == "trend_following":
            signals = self.trend_following_signals(data, market_condition)
        elif strategy_mode == "mean_reversion":
            signals = self.mean_reversion_signals(data, market_condition)
        elif strategy_mode == "breakout_scalping":
            signals = self.breakout_scalping_signals(data, market_condition)
        else:
            # Conservative mode - no signals
            signals = {'buy': False, 'sell': False, 'strength': 0, 'confidence': 0}
        
        # Multi-timeframe confirmation
        if higher_tf_data is not None and hasattr(market_condition, 'htf_bias'):
            if signals['buy']:
                signals['buy'] = self.mtf_analyzer.confirm_entry('buy', market_condition.htf_bias)
            elif signals['sell']:
                signals['sell'] = self.mtf_analyzer.confirm_entry('sell', market_condition.htf_bias)
        
        # Get risk parameters
        if signals['buy'] or signals['sell']:
            risk_params = self.get_adaptive_risk_params(data, market_condition, signals['strength'])
        else:
            risk_params = {}
        
        return {
            'signals': signals,
            'market_condition': market_condition,
            'strategy_mode': strategy_mode,
            'risk_params': risk_params,
            'meta': {
                'regime': market_condition.regime.value,
                'confidence': market_condition.confidence,
                'volatility_percentile': market_condition.volatility_percentile
            }
        }
    
    def update_performance(self, regime: MarketRegime, pnl: float):
        """Update performance tracking by regime"""
        if pnl > 0:
            self.regime_performance[regime]['wins'] += 1
        else:
            self.regime_performance[regime]['losses'] += 1
        
        self.regime_performance[regime]['pnl'] += pnl
    
    def get_regime_stats(self) -> Dict:
        """Get performance statistics by regime"""
        stats = {}
        for regime, data in self.regime_performance.items():
            total_trades = data['wins'] + data['losses']
            win_rate = data['wins'] / total_trades if total_trades > 0 else 0
            avg_pnl = data['pnl'] / total_trades if total_trades > 0 else 0
            
            stats[regime.value] = {
                'total_trades': total_trades,
                'win_rate': win_rate,
                'avg_pnl': avg_pnl,
                'total_pnl': data['pnl']
            }
        
        return stats

if __name__ == "__main__":
    print("🚀 ADAPTIVE ALPHAONE STRATEGY")
    print("✅ Multi-Regime Detection")
    print("✅ Trend Following Mode")
    print("✅ Mean Reversion Mode") 
    print("✅ Breakout Scalping Mode")
    print("✅ Multi-Timeframe Confirmation")
    print("✅ Adaptive Risk Management")
    print("\nReady for integration with existing system!")
