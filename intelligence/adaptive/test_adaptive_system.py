
#!/usr/bin/env python3
"""
ADAPTIVE SYSTEM TESTING SCRIPT
Tests all adaptive components with sample data
"""

import pandas as pd
import numpy as np
import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def generate_sample_data(periods=200):
    """Generate sample OHLCV data for testing"""
    dates = pd.date_range('2024-01-01', periods=periods, freq='5min')
    
    # Generate realistic price data
    np.random.seed(42)
    returns = np.random.normal(0, 0.01, periods)
    price = 100 * np.exp(np.cumsum(returns))
    
    # Generate OHLC from price
    data = pd.DataFrame({
        'open': price * (1 + np.random.normal(0, 0.002, periods)),
        'high': price * (1 + np.abs(np.random.normal(0, 0.005, periods))),
        'low': price * (1 - np.abs(np.random.normal(0, 0.005, periods))),
        'close': price,
        'volume': np.random.randint(1000, 10000, periods)
    }, index=dates)
    
    # Ensure OHLC consistency
    data['high'] = data[['open', 'high', 'close']].max(axis=1)
    data['low'] = data[['open', 'low', 'close']].min(axis=1)
    
    return data

def test_regime_detection():
    """Test regime detection components"""
    print("🔍 Testing Regime Detection...")
    
    try:
        from adaptive_framework import RegimeDetector
        
        # Generate test data
        data = generate_sample_data(100)
        detector = RegimeDetector()
        
        # Test regime detection
        market_condition = detector.detect_regime(data)
        
        print(f"✅ Regime Detection Working!")
        print(f"   Detected Regime: {market_condition.regime.value}")
        print(f"   Confidence: {market_condition.confidence:.2f}")
        print(f"   Volatility Percentile: {market_condition.volatility_percentile:.1f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Regime Detection Error: {e}")
        return False

def test_adaptive_indicators():
    """Test adaptive indicators"""
    print("📊 Testing Adaptive Indicators...")
    
    try:
        from adaptive_framework import AdaptiveIndicators, RegimeDetector, MarketCondition, MarketRegime
        
        data = generate_sample_data(100)
        detector = RegimeDetector()
        market_condition = detector.detect_regime(data)
        
        # Test adaptive ATR stops
        stop_distance, target_distance = AdaptiveIndicators.adaptive_atr_stops(data)
        
        # Test adaptive Bollinger Bands
        bb_upper, bb_middle, bb_lower = AdaptiveIndicators.adaptive_bollinger_bands(data, market_condition)
        
        print(f"✅ Adaptive Indicators Working!")
        print(f"   ATR Stop Distance: {stop_distance:.4f}")
        print(f"   ATR Target Distance: {target_distance:.4f}")
        print(f"   BB Bands Generated: {len(bb_upper)} periods")
        
        return True
        
    except Exception as e:
        print(f"❌ Adaptive Indicators Error: {e}")
        return False

def test_adaptive_strategy():
    """Test adaptive strategy"""
    print("🚀 Testing Adaptive Strategy...")
    
    try:
        from strategies.adaptive_alphaone_strategy import AdaptiveAlphaOneStrategy
        
        config = {'capital': 100000, 'risk_per_trade': 0.02}
        strategy = AdaptiveAlphaOneStrategy(config)
        
        # Generate test data
        data = generate_sample_data(100)
        
        # Test signal generation
        result = strategy.generate_signals(data)
        
        print(f"✅ Adaptive Strategy Working!")
        print(f"   Strategy Mode: {result['strategy_mode']}")
        print(f"   Market Regime: {result['market_condition'].regime.value}")
        print(f"   Buy Signal: {result['signals']['buy']}")
        print(f"   Sell Signal: {result['signals']['sell']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Adaptive Strategy Error: {e}")
        return False

def test_ml_components():
    """Test ML components if available"""
    print("🧠 Testing ML Components...")
    
    try:
        from ml_regime_detector import MLRegimeDetector
        
        detector = MLRegimeDetector(n_regimes=4)
        data = generate_sample_data(150)  # Need more data for ML
        
        result = detector.detect_current_regime(data)
        
        print(f"✅ ML Regime Detection Working!")
        print(f"   Consensus Regime: {result['consensus_regime']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Method: {result['method']}")
        
        return True
        
    except Exception as e:
        print(f"⚠️  ML Components Not Available: {e}")
        print("   Install scikit-learn and hmmlearn for ML features")
        return False

def main():
    """Run all tests"""
    print("🧪 ADAPTIVE SYSTEM TESTING")
    print("=" * 50)
    
    results = []
    results.append(test_regime_detection())
    results.append(test_adaptive_indicators())
    results.append(test_adaptive_strategy())
    results.append(test_ml_components())
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Adaptive system ready!")
    elif passed >= 3:
        print("✅ Core adaptive features working!")
    else:
        print("⚠️  Some components need attention")
    
    return passed >= 3

if __name__ == "__main__":
    main()
