
"""
ADAPTIVE STRATEGY WRAPPER
Integrates adaptive strategies with existing paper trading system
"""

import sys
import os
import numpy as np
import pandas as pd
import talib
import yaml

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from strategies.base_strategy import BaseStrategy
from adaptive_framework import RegimeDetector, MarketRegime
from strategies.adaptive_alphaone_strategy import AdaptiveAlphaOneStrategy

class AdaptiveStrategyWrapper(BaseStrategy):
    """
    Wrapper to integrate adaptive strategies with existing system
    """
    
    def __init__(self, df: pd.DataFrame, symbol: str = None, logger=None, 
                 primary_timeframe: int = 5, **kwargs):
        super().__init__(df, symbol=symbol, logger=logger, primary_timeframe=primary_timeframe)
        self.name = "AdaptiveStrategyWrapper"
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
    
    def calculate_indicators(self):
        """Required by BaseStrategy - resample and calculate indicators"""
        if self.df_1min_raw.empty:
            self.df = pd.DataFrame()
            return
            
        # Resample to primary timeframe (data is already indexed properly)
        tf_string = f'{self.primary_timeframe}T'
        self.df = self.df_1min_raw.resample(tf_string).agg({
            'open': 'first',
            'high': 'max', 
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        if len(self.df) < 20:
            return
            
        # Simple indicators
        self.df['sma_20'] = talib.SMA(self.df['close'], timeperiod=20)
        self.df['rsi'] = talib.RSI(self.df['close'], timeperiod=14)
        
    def generate_signals(self):
        """Required by BaseStrategy - generate trading signals"""
        if len(self.df) < 20:
            return
            
        # Initialize columns
        self.df['entry_signal'] = 'NONE'
        self.df['stop_loss'] = np.nan
        self.df['target'] = np.nan
        
        # Simple wrapper signals
        last_idx = len(self.df) - 1
        rsi = self.df['rsi'].iloc[last_idx]
        close = self.df['close'].iloc[last_idx]
        
        if rsi < 35:
            self.df.loc[last_idx, 'entry_signal'] = 'BUY'
            self.df.loc[last_idx, 'stop_loss'] = close * 0.98
            self.df.loc[last_idx, 'target'] = close * 1.03
        elif rsi > 65:
            self.df.loc[last_idx, 'entry_signal'] = 'SELL'
            self.df.loc[last_idx, 'stop_loss'] = close * 1.02
            self.df.loc[last_idx, 'target'] = close * 0.97
