"""
ENHANCED MORNING VALIDATION - Integrated with Pre-Market Intelligence
Combines parameter validation with comprehensive pre-market analysis
"""

import sys
import os
import json
import yaml
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Tuple, List

# Import our pre-market intelligence system
from premarket_intelligence import PreMarketIntelligenceSystem

logger = logging.getLogger(__name__)

class EnhancedMorningValidation:
    """
    Enhanced morning validation system that integrates:
    1. Parameter validation from evening optimization
    2. Pre-market intelligence analysis
    3. News sentiment impact
    4. Global market conditions
    5. Risk-adjusted recommendations
    """
    
    def __init__(self, config_path: str = 'config.yml'):
        self.config_path = config_path
        self.load_config()
        self.intelligence_system = PreMarketIntelligenceSystem()
        self.params_file = 'optimized_parameters.json'
        self.validation_file = 'enhanced_morning_validation.json'
        
    def load_config(self):
        """Load configuration"""
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def comprehensive_morning_analysis(self) -> Dict[str, Any]:
        """
        Comprehensive morning analysis combining all factors
        """
        logger.info("🌅 Starting Enhanced Morning Validation")
        start_time = datetime.now()
        
        # Step 1: Load yesterday's optimized parameters
        yesterday_params = self.load_yesterday_parameters()
        
        # Step 2: Get comprehensive pre-market intelligence
        intelligence_report = self.intelligence_system.get_comprehensive_premarket_analysis()
        
        # Step 3: Validate parameters against current conditions
        parameter_validation = self.validate_parameters_with_intelligence(
            yesterday_params, intelligence_report
        )
        
        # Step 4: Generate enhanced recommendations
        enhanced_recommendations = self.generate_enhanced_recommendations(
            parameter_validation, intelligence_report
        )
        
        # Step 5: Apply intelligent adjustments
        final_parameters = self.apply_intelligent_adjustments(
            yesterday_params['strategy_parameters'],
            intelligence_report,
            enhanced_recommendations
        )
        
        # Step 6: Generate trading plan
        trading_plan = self.generate_daily_trading_plan(
            final_parameters, intelligence_report, enhanced_recommendations
        )
        
        # Compile comprehensive result
        comprehensive_result = {
            'timestamp': datetime.now().isoformat(),
            'validation_duration': (datetime.now() - start_time).total_seconds(),
            'intelligence_report': intelligence_report,
            'parameter_validation': parameter_validation,
            'enhanced_recommendations': enhanced_recommendations,
            'final_parameters': final_parameters,
            'trading_plan': trading_plan,
            'trading_ready': True,
            'confidence_score': self.calculate_confidence_score(intelligence_report)
        }
        
        # Save comprehensive validation
        with open(self.validation_file, 'w') as f:
            json.dump(comprehensive_result, f, indent=2, default=str)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"🎉 Enhanced morning validation complete in {duration:.1f} seconds")
        
        return comprehensive_result
    
    def load_yesterday_parameters(self) -> Dict:
        """Load yesterday's optimized parameters"""
        if not os.path.exists(self.params_file):
            logger.error("❌ No optimized parameters found!")
            return self.get_emergency_parameters()
        
        with open(self.params_file, 'r') as f:
            return json.load(f)
    
    def validate_parameters_with_intelligence(self, yesterday_params: Dict, intelligence: Dict) -> Dict:
        """
        Validate parameters using intelligence report
        """
        logger.info("🔍 Validating parameters with pre-market intelligence...")
        
        validation_result = {
            'base_validation': self.basic_parameter_validation(yesterday_params),
            'news_impact': self.assess_news_impact(intelligence['news_sentiment']),
            'global_market_impact': self.assess_global_impact(intelligence['global_markets']),
            'risk_assessment': intelligence['risk_assessment'],
            'currency_impact': self.assess_currency_impact(intelligence['currency_analysis']),
            'technical_alignment': self.assess_technical_alignment(intelligence['technical_signals'])
        }
        
        # Determine overall validation action
        validation_result['recommended_action'] = self.determine_validation_action(validation_result)
        
        return validation_result
    
    def generate_enhanced_recommendations(self, validation: Dict, intelligence: Dict) -> Dict:
        """
        Generate enhanced recommendations based on all factors
        """
        logger.info("💡 Generating enhanced recommendations...")
        
        recommendations = {
            'position_sizing': self.recommend_position_sizing(validation, intelligence),
            'strategy_selection': self.recommend_strategy_selection(validation, intelligence),
            'risk_management': self.recommend_risk_management(validation, intelligence),
            'market_timing': self.recommend_market_timing(validation, intelligence),
            'sector_focus': self.recommend_sector_focus(intelligence),
            'exit_strategy': self.recommend_exit_strategy(validation, intelligence)
        }
        
        return recommendations
    
    def apply_intelligent_adjustments(self, base_params: Dict, intelligence: Dict, recommendations: Dict) -> Dict:
        """
        Apply intelligent adjustments to parameters
        """
        logger.info("⚙️ Applying intelligent parameter adjustments...")
        
        adjusted_params = {}
        
        for strategy_name, params in base_params.items():
            adjusted_params[strategy_name] = self.adjust_strategy_parameters(
                strategy_name, params, intelligence, recommendations
            )
        
        return adjusted_params
    
    def adjust_strategy_parameters(self, strategy_name: str, params: Dict, intelligence: Dict, recommendations: Dict) -> Dict:
        """
        Adjust individual strategy parameters
        """
        adjusted = params.copy()
        
        # Position sizing adjustments
        position_multiplier = self.get_position_multiplier(recommendations['position_sizing'])
        if 'position_size' in adjusted:
            adjusted['position_size'] = float(adjusted['position_size']) * position_multiplier
        
        # Risk management adjustments
        risk_multiplier = self.get_risk_multiplier(recommendations['risk_management'])
        if 'stop_loss' in adjusted:
            adjusted['stop_loss'] = float(adjusted['stop_loss']) * risk_multiplier
        
        # Entry/exit threshold adjustments based on volatility
        volatility_adj = self.get_volatility_adjustment(intelligence)
        if 'entry_threshold' in adjusted:
            adjusted['entry_threshold'] = float(adjusted['entry_threshold']) * volatility_adj
        if 'exit_threshold' in adjusted:
            adjusted['exit_threshold'] = float(adjusted['exit_threshold']) * volatility_adj
        
        # News sentiment adjustments
        sentiment_adj = self.get_sentiment_adjustment(intelligence['news_sentiment'])
        if 'confidence_threshold' in adjusted:
            adjusted['confidence_threshold'] = float(adjusted.get('confidence_threshold', 0.7)) * sentiment_adj
        
        # Add adjustment metadata
        adjusted['adjustment_metadata'] = {
            'position_multiplier': position_multiplier,
            'risk_multiplier': risk_multiplier,
            'volatility_adjustment': volatility_adj,
            'sentiment_adjustment': sentiment_adj,
            'adjusted_at': datetime.now().isoformat()
        }
        
        return adjusted
    
    def generate_daily_trading_plan(self, final_params: Dict, intelligence: Dict, recommendations: Dict) -> Dict:
        """
        Generate comprehensive daily trading plan
        """
        trading_plan = {
            'market_outlook': self.generate_market_outlook(intelligence),
            'strategy_allocation': self.generate_strategy_allocation(final_params, recommendations),
            'risk_limits': self.generate_risk_limits(recommendations),
            'key_levels': intelligence['technical_signals'].get('key_levels', {}),
            'watch_list': self.generate_watch_list(intelligence),
            'exit_plan': self.generate_exit_plan(recommendations),
            'contingency_plans': self.generate_contingency_plans(intelligence)
        }
        
        return trading_plan
    
    # Assessment methods
    def assess_news_impact(self, news_sentiment: Dict) -> Dict:
        """Assess impact of news sentiment"""
        sentiment = news_sentiment['overall_sentiment']
        category = news_sentiment['sentiment_category']
        
        impact_level = "LOW"
        if abs(sentiment) > 0.3:
            impact_level = "HIGH"
        elif abs(sentiment) > 0.1:
            impact_level = "MEDIUM"
        
        return {
            'impact_level': impact_level,
            'sentiment_score': sentiment,
            'category': category,
            'adjustment_needed': impact_level != "LOW"
        }
    
    def assess_global_impact(self, global_markets: Dict) -> Dict:
        """Assess global market impact"""
        avg_change = global_markets['average_change']
        volatility = global_markets['volatility']
        
        impact_level = "LOW"
        if abs(avg_change) > 1.5 or volatility > 2.5:
            impact_level = "HIGH"
        elif abs(avg_change) > 0.75 or volatility > 1.5:
            impact_level = "MEDIUM"
        
        return {
            'impact_level': impact_level,
            'global_bias': global_markets['global_bias'],
            'volatility': volatility,
            'adjustment_needed': impact_level != "LOW"
        }
    
    def assess_currency_impact(self, currency_analysis: Dict) -> Dict:
        """Assess currency impact"""
        usd_change = abs(currency_analysis['usd_change_percent'])
        
        impact_level = "LOW"
        if usd_change > 1.0:
            impact_level = "HIGH"
        elif usd_change > 0.5:
            impact_level = "MEDIUM"
        
        return {
            'impact_level': impact_level,
            'usd_change': currency_analysis['usd_change_percent'],
            'equity_impact': currency_analysis['equity_impact'],
            'adjustment_needed': impact_level != "LOW"
        }
    
    def assess_technical_alignment(self, technical_signals: Dict) -> Dict:
        """Assess technical signal alignment"""
        market_bias = technical_signals['market_bias']
        bullish_ratio = technical_signals['bullish_ratio']
        
        alignment_strength = "WEAK"
        if bullish_ratio > 0.7 or bullish_ratio < 0.3:
            alignment_strength = "STRONG"
        elif bullish_ratio > 0.6 or bullish_ratio < 0.4:
            alignment_strength = "MODERATE"
        
        return {
            'alignment_strength': alignment_strength,
            'market_bias': market_bias,
            'bullish_ratio': bullish_ratio,
            'adjustment_needed': alignment_strength == "STRONG"
        }
    
    # Recommendation methods
    def recommend_position_sizing(self, validation: Dict, intelligence: Dict) -> str:
        """Recommend position sizing"""
        risk_level = intelligence['risk_assessment']['risk_level']
        
        if risk_level == "HIGH":
            return "REDUCE_SIGNIFICANT"  # 50% reduction
        elif risk_level == "MEDIUM":
            return "REDUCE_MODERATE"     # 25% reduction
        else:
            # Check for positive conditions
            news_positive = intelligence['news_sentiment']['sentiment_category'] == "POSITIVE"
            global_positive = intelligence['global_markets']['global_bias'] == "POSITIVE"
            
            if news_positive and global_positive:
                return "INCREASE_MODERATE"  # 25% increase
            else:
                return "NORMAL"
    
    def recommend_strategy_selection(self, validation: Dict, intelligence: Dict) -> str:
        """Recommend strategy selection"""
        global_bias = intelligence['global_markets']['global_bias']
        risk_level = intelligence['risk_assessment']['risk_level']
        
        if risk_level == "HIGH":
            return "CONSERVATIVE"
        elif global_bias == "POSITIVE":
            return "TREND_FOLLOWING"
        elif global_bias == "NEGATIVE":
            return "MEAN_REVERSION"
        else:
            return "BALANCED"
    
    def recommend_risk_management(self, validation: Dict, intelligence: Dict) -> str:
        """Recommend risk management approach"""
        volatility = intelligence['global_markets']['volatility']
        risk_level = intelligence['risk_assessment']['risk_level']
        
        if risk_level == "HIGH" or volatility > 2.0:
            return "TIGHT"      # 1.5x tighter stops
        elif volatility < 1.0:
            return "RELAXED"    # 0.8x normal stops
        else:
            return "STANDARD"   # Normal stops
    
    # Helper methods
    def get_position_multiplier(self, recommendation: str) -> float:
        """Get position size multiplier"""
        multipliers = {
            'REDUCE_SIGNIFICANT': 0.5,
            'REDUCE_MODERATE': 0.75,
            'NORMAL': 1.0,
            'INCREASE_MODERATE': 1.25,
            'INCREASE_SIGNIFICANT': 1.5
        }
        return multipliers.get(recommendation, 1.0)
    
    def get_risk_multiplier(self, recommendation: str) -> float:
        """Get risk management multiplier"""
        multipliers = {
            'TIGHT': 1.5,      # Tighter stops
            'STANDARD': 1.0,
            'RELAXED': 0.8     # Wider stops
        }
        return multipliers.get(recommendation, 1.0)
    
    def calculate_confidence_score(self, intelligence: Dict) -> float:
        """Calculate overall confidence score"""
        factors = [
            intelligence['news_sentiment'].get('sentiment_category') == 'POSITIVE',
            intelligence['global_markets'].get('global_bias') == 'POSITIVE',
            intelligence['risk_assessment'].get('risk_level') == 'LOW',
            intelligence['currency_analysis'].get('equity_impact') != 'NEGATIVE_FOR_EQUITY'
        ]
        
        return sum(factors) / len(factors)
    
    # Placeholder methods (to be implemented based on specific requirements)
    def basic_parameter_validation(self, params: Dict) -> Dict:
        return {'action': 'VALIDATE', 'reason': 'Standard validation'}
    
    def determine_validation_action(self, validation: Dict) -> str:
        return 'APPLY_INTELLIGENT_ADJUSTMENTS'
    
    def recommend_market_timing(self, validation: Dict, intelligence: Dict) -> str:
        return 'NORMAL_OPEN'
    
    def recommend_sector_focus(self, intelligence: Dict) -> List[str]:
        return ['BANKING', 'IT', 'AUTO']
    
    def recommend_exit_strategy(self, validation: Dict, intelligence: Dict) -> str:
        return 'STANDARD'
    
    def generate_market_outlook(self, intelligence: Dict) -> str:
        return f"Market outlook: {intelligence['global_markets']['global_bias']}"
    
    def generate_strategy_allocation(self, params: Dict, recommendations: Dict) -> Dict:
        return {'equal_weight': True}
    
    def generate_risk_limits(self, recommendations: Dict) -> Dict:
        return {'max_risk_per_trade': 0.02}
    
    def generate_watch_list(self, intelligence: Dict) -> List[str]:
        return ['RELIANCE', 'TCS', 'INFY']
    
    def generate_exit_plan(self, recommendations: Dict) -> Dict:
        return {'eod_exit': True}
    
    def generate_contingency_plans(self, intelligence: Dict) -> Dict:
        return {'high_volatility_plan': 'Reduce positions'}
    
    def get_emergency_parameters(self) -> Dict:
        return {'strategy_parameters': {}}
    
    def get_volatility_adjustment(self, intelligence: Dict) -> float:
        return 1.0
    
    def get_sentiment_adjustment(self, sentiment: Dict) -> float:
        return 1.0

if __name__ == "__main__":
    print("🌅 ENHANCED MORNING VALIDATION SYSTEM")
    print("=" * 50)
    
    validator = EnhancedMorningValidation()
    result = validator.comprehensive_morning_analysis()
    
    print("✅ Enhanced validation complete!")
    print(f"Confidence Score: {result['confidence_score']:.2f}")
    print(f"Trading Ready: {result['trading_ready']}")
