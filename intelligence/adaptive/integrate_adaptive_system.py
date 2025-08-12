"""
INTEGRATION SCRIPT - Connect All Advanced Components
Integrates adaptive framework with existing strategies and trading system
"""

import sys
import os
import yaml
import pandas as pd
from typing import Dict, Any

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import adaptive components
try:
    from adaptive_framework import RegimeDetector, MarketRegime, AdaptiveIndicators, MultiTimeframeAnalysis
    from strategies.adaptive_alphaone_strategy import AdaptiveAlphaOneStrategy
    from ml_regime_detector import MLRegimeDetector, StatisticalRegimeDetector
except ImportError as e:
    print(f"Import error: {e}")
    print("Installing required packages...")

def install_required_packages():
    """Install ML packages if not available"""
    packages = [
        'scikit-learn',
        'hmmlearn', 
        'numpy',
        'pandas'
    ]
    
    for package in packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            print(f"Installing {package}...")
            os.system(f"pip install {package}")

def create_enhanced_config():
    """Create enhanced configuration with adaptive settings"""
    enhanced_config = {
        'adaptive_trading': {
            'enabled': True,
            'regime_detection': {
                'method': 'hybrid',  # 'basic', 'ml', 'statistical', 'hybrid'
                'lookback_period': 50,
                'confidence_threshold': 0.6,
                'regime_update_frequency': 5  # Update every 5 candles
            },
            'multi_timeframe': {
                'enabled': True,
                'primary_timeframe': '5m',
                'confirmation_timeframe': '15m',
                'higher_timeframe': '1h'
            },
            'adaptive_indicators': {
                'dynamic_periods': True,
                'volatility_adjustment': True,
                'regime_based_parameters': True
            },
            'risk_management': {
                'adaptive_position_sizing': True,
                'regime_based_stops': True,
                'dynamic_risk_reward': True,
                'max_risk_per_trade': 0.02,  # 2% per trade
                'volatility_scaling': True
            }
        },
        'regime_strategies': {
            'trending_bullish': {
                'primary': 'trend_following',
                'indicators': ['ma_crossover', 'macd', 'adx'],
                'risk_multiplier': 1.0,
                'position_size_multiplier': 1.0
            },
            'trending_bearish': {
                'primary': 'trend_following',
                'indicators': ['ma_crossover', 'macd', 'adx'],
                'risk_multiplier': 1.0,
                'position_size_multiplier': 0.8  # Smaller positions in bear trends
            },
            'range_bound': {
                'primary': 'mean_reversion',
                'indicators': ['rsi', 'bollinger_bands', 'stochastic'],
                'risk_multiplier': 0.7,  # Tighter stops
                'position_size_multiplier': 1.2  # Larger positions in ranges
            },
            'high_volatility': {
                'primary': 'breakout_scalping',
                'indicators': ['atr', 'volume', 'support_resistance'],
                'risk_multiplier': 1.5,  # Wider stops
                'position_size_multiplier': 0.6  # Smaller positions
            },
            'low_volatility': {
                'primary': 'narrow_range_breakout',
                'indicators': ['bollinger_squeeze', 'atr', 'volume'],
                'risk_multiplier': 0.8,
                'position_size_multiplier': 1.0
            }
        },
        'ml_settings': {
            'enabled': False,  # Start with False, enable after testing
            'models': ['kmeans', 'hmm'],
            'feature_engineering': True,
            'ensemble_method': True,
            'retrain_frequency': 'weekly'
        }
    }
    
    return enhanced_config

def update_existing_config():
    """Update existing config.yml with adaptive settings"""
    config_path = '/home/ubuntu/PaperTradingV1.3/config.yml'
    
    # Load existing config
    with open(config_path, 'r') as f:
        existing_config = yaml.safe_load(f)
    
    # Add adaptive settings
    enhanced_config = create_enhanced_config()
    existing_config.update(enhanced_config)
    
    # Save enhanced config
    enhanced_config_path = '/home/ubuntu/PaperTradingV1.3/enhanced_config.yml'
    with open(enhanced_config_path, 'w') as f:
        yaml.dump(existing_config, f, default_flow_style=False, indent=2)
    
    print(f"✅ Enhanced config saved to: {enhanced_config_path}")
    return enhanced_config_path

def create_adaptive_strategy_wrapper():
    """Create wrapper to integrate adaptive strategies with existing system"""
    wrapper_code = '''
"""
ADAPTIVE STRATEGY WRAPPER
Integrates adaptive strategies with existing paper trading system
"""

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from strategies.base_strategy import BaseStrategy
from adaptive_framework import RegimeDetector, MarketRegime
from strategies.adaptive_alphaone_strategy import AdaptiveAlphaOneStrategy
import pandas as pd
import yaml

class AdaptiveStrategyWrapper(BaseStrategy):
    """
    Wrapper to integrate adaptive strategies with existing system
    """
    
    def __init__(self, config):
        super().__init__(config)
        self.adaptive_strategy = AdaptiveAlphaOneStrategy(config)
        self.regime_detector = RegimeDetector()
        
        # Load enhanced config if available
        try:
            with open('enhanced_config.yml', 'r') as f:
                self.enhanced_config = yaml.safe_load(f)
                self.adaptive_enabled = self.enhanced_config.get('adaptive_trading', {}).get('enabled', False)
        except:
            self.adaptive_enabled = False
            print("⚠️  Enhanced config not found, using basic strategy")
    
    def should_buy(self, data: pd.DataFrame) -> bool:
        """Enhanced buy logic with adaptive capabilities"""
        if not self.adaptive_enabled:
            # Fallback to original strategy logic
            return self._original_buy_logic(data)
        
        # Use adaptive strategy
        result = self.adaptive_strategy.generate_signals(data)
        return result['signals']['buy']
    
    def should_sell(self, data: pd.DataFrame) -> bool:
        """Enhanced sell logic with adaptive capabilities"""
        if not self.adaptive_enabled:
            # Fallback to original strategy logic  
            return self._original_sell_logic(data)
        
        # Use adaptive strategy
        result = self.adaptive_strategy.generate_signals(data)
        return result['signals']['sell']
    
    def get_adaptive_info(self, data: pd.DataFrame) -> dict:
        """Get adaptive strategy information"""
        if not self.adaptive_enabled:
            return {'mode': 'basic', 'regime': 'unknown'}
        
        result = self.adaptive_strategy.generate_signals(data)
        return {
            'mode': result['strategy_mode'],
            'regime': result['market_condition'].regime.value,
            'confidence': result['market_condition'].confidence,
            'risk_params': result.get('risk_params', {})
        }
    
    def _original_buy_logic(self, data: pd.DataFrame) -> bool:
        """Original buy logic as fallback"""
        # Implement original strategy logic here
        # This is a placeholder - replace with actual logic
        return False
    
    def _original_sell_logic(self, data: pd.DataFrame) -> bool:
        """Original sell logic as fallback"""
        # Implement original strategy logic here
        # This is a placeholder - replace with actual logic
        return False
'''
    
    wrapper_path = '/home/ubuntu/PaperTradingV1.3/strategies/adaptive_strategy_wrapper.py'
    with open(wrapper_path, 'w') as f:
        f.write(wrapper_code)
    
    print(f"✅ Adaptive strategy wrapper created: {wrapper_path}")
    return wrapper_path

def create_testing_script():
    """Create testing script for adaptive components"""
    test_code = '''
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
    
    print("\\n" + "=" * 50)
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
'''
    
    test_path = '/home/ubuntu/PaperTradingV1.3/test_adaptive_system.py'
    with open(test_path, 'w') as f:
        f.write(test_code)
    
    print(f"✅ Testing script created: {test_path}")
    return test_path

def main():
    """Main integration function"""
    print("🚀 ADAPTIVE TRADING SYSTEM INTEGRATION")
    print("=" * 60)
    
    # Install required packages
    print("📦 Installing required packages...")
    install_required_packages()
    
    # Update configuration
    print("⚙️  Updating configuration...")
    enhanced_config_path = update_existing_config()
    
    # Create strategy wrapper
    print("🔄 Creating strategy wrapper...")
    wrapper_path = create_adaptive_strategy_wrapper()
    
    # Create testing script
    print("🧪 Creating testing script...")
    test_path = create_testing_script()
    
    print("\\n" + "=" * 60)
    print("✅ INTEGRATION COMPLETE!")
    print("\\n📁 Files Created:")
    print(f"   • {enhanced_config_path}")
    print(f"   • {wrapper_path}")
    print(f"   • {test_path}")
    print("   • adaptive_framework.py")
    print("   • strategies/adaptive_alphaone_strategy.py")
    print("   • ml_regime_detector.py")
    
    print("\\n🚀 Next Steps:")
    print("   1. Run: python3 test_adaptive_system.py")
    print("   2. Test individual components")
    print("   3. Enable adaptive_trading in enhanced_config.yml")
    print("   4. Update daily automation to use enhanced config")
    
    return True

if __name__ == "__main__":
    main()
