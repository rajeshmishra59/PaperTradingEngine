#!/usr/bin/env python3
"""
HYBRID OPTIMIZATION SYSTEM - Evening Full + Morning Validation
Implements the optimal timing strategy for paper trading automation
"""

import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import subprocess
import logging
from typing import Dict, Any, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HybridOptimizationSystem:
    """
    Hybrid optimization system:
    - Evening: Full comprehensive optimization
    - Morning: Quick validation and parameter adjustment
    """
    
    def __init__(self, config_path: str = 'config.yml'):
        self.config_path = config_path
        self.load_config()
        self.params_file = 'optimized_parameters.json'
        self.validation_file = 'morning_validation.json'
        
    def load_config(self):
        """Load configuration"""
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def evening_full_optimization(self) -> Dict[str, Any]:
        """
        Evening comprehensive optimization
        Run after market close (post 3:30 PM)
        """
        logger.info("🌙 Starting Evening Full Optimization")
        start_time = datetime.now()
        
        optimization_results = {}
        
        # Get today's market data for optimization
        market_data = self._get_today_market_data()
        current_regime = self._detect_market_regime(market_data)
        
        logger.info(f"📊 Market Regime Detected: {current_regime}")
        
        # Optimize all strategies
        for strategy_name, strategy_config in self.config['strategy_config'].items():
            logger.info(f"🎯 Optimizing {strategy_name}...")
            
            strategy_results = self._optimize_strategy(
                strategy_name, 
                strategy_config, 
                market_data,
                current_regime
            )
            
            optimization_results[strategy_name] = strategy_results
            logger.info(f"✅ {strategy_name} optimization complete")
        
        # Save results with metadata
        optimization_metadata = {
            'optimization_date': datetime.now().isoformat(),
            'market_regime': current_regime,
            'optimization_duration': (datetime.now() - start_time).total_seconds(),
            'data_quality_score': self._calculate_data_quality(market_data),
            'vix_level': self._get_vix_level(),
            'market_summary': self._get_market_summary(market_data)
        }
        
        full_results = {
            'metadata': optimization_metadata,
            'strategy_parameters': optimization_results
        }
        
        # Save optimized parameters
        with open(self.params_file, 'w') as f:
            json.dump(full_results, f, indent=2, default=str)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"🎉 Evening optimization complete in {duration:.1f} seconds")
        logger.info(f"💾 Parameters saved to {self.params_file}")
        
        return full_results
    
    def morning_quick_validation(self) -> Dict[str, Any]:
        """
        Morning quick validation
        Run at 9:00 AM before market open
        """
        logger.info("🌅 Starting Morning Quick Validation")
        start_time = datetime.now()
        
        # Load yesterday's optimized parameters
        if not os.path.exists(self.params_file):
            logger.error("❌ No optimized parameters found! Run evening optimization first.")
            return self._emergency_fallback()
        
        with open(self.params_file, 'r') as f:
            yesterday_results = json.load(f)
        
        # Get current pre-market data
        current_data = self._get_premarket_data()
        
        # Perform validation checks
        validation_result = self._validate_parameters(yesterday_results, current_data)
        
        # Execute validation decision
        if validation_result['action'] == 'USE_YESTERDAY_PARAMS':
            logger.info("✅ Yesterday's parameters validated - proceeding")
            final_params = yesterday_results['strategy_parameters']
            
        elif validation_result['action'] == 'ADJUST_RISK_PARAMS':
            logger.info("⚙️ Adjusting risk parameters for market conditions")
            final_params = self._adjust_risk_parameters(
                yesterday_results['strategy_parameters'],
                validation_result['adjustment_factor']
            )
            
        elif validation_result['action'] == 'VALIDATE_PARAMETERS':
            logger.info("🔍 Re-validating parameters for regime change")
            final_params = self._revalidate_for_regime(
                yesterday_results['strategy_parameters'],
                validation_result['new_regime']
            )
            
        elif validation_result['action'] == 'QUICK_REOPTIMIZE':
            logger.info("⚡ Quick re-optimization required")
            final_params = self._quick_reoptimization(current_data)
            
        else:
            logger.warning("⚠️ Unknown validation action - using yesterday's parameters")
            final_params = yesterday_results['strategy_parameters']
        
        # Save validation results
        validation_metadata = {
            'validation_date': datetime.now().isoformat(),
            'validation_action': validation_result['action'],
            'validation_reason': validation_result['reason'],
            'validation_duration': (datetime.now() - start_time).total_seconds(),
            'market_gap': validation_result.get('gap_percentage', 0),
            'regime_change': validation_result.get('regime_changed', False)
        }
        
        validation_output = {
            'metadata': validation_metadata,
            'strategy_parameters': final_params,
            'trading_ready': True
        }
        
        with open(self.validation_file, 'w') as f:
            json.dump(validation_output, f, indent=2, default=str)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"🎉 Morning validation complete in {duration:.1f} seconds")
        
        return validation_output
    
    def _get_today_market_data(self) -> pd.DataFrame:
        """Get today's complete market data for optimization"""
        # Placeholder - implement actual data fetching
        logger.info("📊 Loading today's market data...")
        # This would connect to your data source
        return pd.DataFrame()  # Replace with actual implementation
    
    def _get_premarket_data(self) -> pd.DataFrame:
        """Get pre-market data for validation"""
        logger.info("📈 Loading pre-market data...")
        # This would get overnight/pre-market data
        return pd.DataFrame()  # Replace with actual implementation
    
    def _detect_market_regime(self, data: pd.DataFrame) -> str:
        """Detect current market regime"""
        # Simplified regime detection
        # Replace with your adaptive_framework implementation
        regimes = ['trending_bullish', 'trending_bearish', 'range_bound', 'high_volatility', 'low_volatility']
        return np.random.choice(regimes)  # Placeholder
    
    def _optimize_strategy(self, strategy_name: str, config: Dict, data: pd.DataFrame, regime: str) -> Dict:
        """Optimize a single strategy"""
        logger.info(f"🔧 Running optimization for {strategy_name}")
        
        # This would call your actual optimization logic
        # For now, return mock optimized parameters
        optimized_params = {
            'entry_threshold': np.random.uniform(0.01, 0.05),
            'exit_threshold': np.random.uniform(0.01, 0.03),
            'stop_loss': np.random.uniform(0.02, 0.05),
            'position_size': np.random.uniform(0.1, 0.3),
            'optimization_score': np.random.uniform(0.6, 0.9),
            'regime_optimized_for': regime
        }
        
        return optimized_params
    
    def _validate_parameters(self, yesterday_results: Dict, current_data: pd.DataFrame) -> Dict:
        """Validate if yesterday's parameters are still good"""
        
        yesterday_metadata = yesterday_results['metadata']
        yesterday_regime = yesterday_metadata.get('market_regime', 'unknown')
        yesterday_vix = yesterday_metadata.get('vix_level', 20)
        
        # Current market analysis
        current_regime = self._detect_market_regime(current_data)
        current_vix = self._get_vix_level()
        gap_percentage = self._calculate_gap(current_data)
        
        # Decision logic
        if gap_percentage > 2.0:
            return {
                'action': 'QUICK_REOPTIMIZE',
                'reason': f'Major gap detected: {gap_percentage:.1f}%',
                'gap_percentage': gap_percentage
            }
        
        vix_change = abs(current_vix - yesterday_vix) / yesterday_vix if yesterday_vix > 0 else 0
        if vix_change > 0.3:
            return {
                'action': 'ADJUST_RISK_PARAMS',
                'reason': f'VIX changed by {vix_change:.1%}',
                'adjustment_factor': min(vix_change, 0.5)  # Cap adjustment
            }
        
        if current_regime != yesterday_regime:
            return {
                'action': 'VALIDATE_PARAMETERS',
                'reason': f'Regime changed: {yesterday_regime} → {current_regime}',
                'new_regime': current_regime,
                'regime_changed': True
            }
        
        return {
            'action': 'USE_YESTERDAY_PARAMS',
            'reason': 'Market conditions stable',
            'regime_changed': False
        }
    
    def _adjust_risk_parameters(self, params: Dict, adjustment_factor: float) -> Dict:
        """Adjust risk parameters based on market conditions"""
        adjusted_params = params.copy()
        
        for strategy_name, strategy_params in adjusted_params.items():
            # Increase stop loss for higher volatility
            if 'stop_loss' in strategy_params:
                strategy_params['stop_loss'] *= (1 + adjustment_factor)
            
            # Reduce position size for higher risk
            if 'position_size' in strategy_params:
                strategy_params['position_size'] *= (1 - adjustment_factor * 0.5)
        
        return adjusted_params
    
    def _revalidate_for_regime(self, params: Dict, new_regime: str) -> Dict:
        """Quick revalidation for regime change"""
        # This could be more sophisticated
        return params  # Simplified for now
    
    def _quick_reoptimization(self, current_data: pd.DataFrame) -> Dict:
        """Quick re-optimization for major market changes"""
        logger.info("⚡ Performing quick re-optimization...")
        
        # Simplified quick optimization
        # In practice, this would run a limited optimization
        quick_params = {}
        for strategy_name in self.config['strategy_config'].keys():
            quick_params[strategy_name] = {
                'entry_threshold': 0.02,  # Conservative defaults
                'exit_threshold': 0.015,
                'stop_loss': 0.03,
                'position_size': 0.15,  # Smaller position for uncertainty
                'optimization_score': 0.5,  # Lower confidence
                'quick_reopt': True
            }
        
        return quick_params
    
    def _emergency_fallback(self) -> Dict:
        """Emergency fallback parameters"""
        logger.warning("🚨 Using emergency fallback parameters")
        
        fallback_params = {
            'metadata': {
                'validation_date': datetime.now().isoformat(),
                'validation_action': 'EMERGENCY_FALLBACK',
                'validation_reason': 'No optimized parameters available'
            },
            'strategy_parameters': {},
            'trading_ready': True
        }
        
        for strategy_name in self.config['strategy_config'].keys():
            fallback_params['strategy_parameters'][strategy_name] = {
                'entry_threshold': 0.025,  # Very conservative
                'exit_threshold': 0.02,
                'stop_loss': 0.035,
                'position_size': 0.1,  # Small position
                'optimization_score': 0.3,  # Low confidence
                'fallback': True
            }
        
        return fallback_params
    
    def _calculate_data_quality(self, data: pd.DataFrame) -> float:
        """Calculate data quality score"""
        return 0.85  # Placeholder
    
    def _get_vix_level(self) -> float:
        """Get current VIX level"""
        return np.random.uniform(15, 25)  # Placeholder
    
    def _get_market_summary(self, data: pd.DataFrame) -> Dict:
        """Get market summary statistics"""
        return {'trend': 'neutral', 'volatility': 'normal'}  # Placeholder
    
    def _calculate_gap(self, data: pd.DataFrame) -> float:
        """Calculate overnight gap percentage"""
        return np.random.uniform(-1, 1)  # Placeholder

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Hybrid Optimization System')
    parser.add_argument('--mode', choices=['evening', 'morning'], required=True,
                       help='Run evening optimization or morning validation')
    
    args = parser.parse_args()
    
    system = HybridOptimizationSystem()
    
    if args.mode == 'evening':
        results = system.evening_full_optimization()
        print("🌙 Evening optimization completed successfully!")
        
    elif args.mode == 'morning':
        results = system.morning_quick_validation()
        print("🌅 Morning validation completed successfully!")
        
        if results['trading_ready']:
            print("✅ System ready for trading!")
        else:
            print("⚠️ Trading readiness check failed!")

if __name__ == "__main__":
    main()
