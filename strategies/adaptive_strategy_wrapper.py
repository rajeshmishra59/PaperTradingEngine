
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
