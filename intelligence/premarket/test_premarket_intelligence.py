#!/usr/bin/env python3
"""
PRE-MARKET INTELLIGENCE TESTING
Test the pre-market analysis system with sample data
"""

import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from premarket_intelligence import PreMarketIntelligenceSystem
    from enhanced_morning_validation import EnhancedMorningValidation
    print("✅ Successfully imported pre-market intelligence modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_premarket_intelligence():
    """Test pre-market intelligence system"""
    print("🌅 Testing Pre-Market Intelligence System")
    print("=" * 50)
    
    try:
        # Initialize intelligence system
        intelligence = PreMarketIntelligenceSystem()
        
        # Get comprehensive analysis
        print("📊 Running comprehensive pre-market analysis...")
        analysis = intelligence.get_comprehensive_premarket_analysis()
        
        print("✅ Pre-market analysis completed!")
        print(f"📰 News sentiment: {analysis['news_sentiment']['sentiment_category']}")
        print(f"🌍 Global market bias: {analysis['global_markets']['global_bias']}")
        print(f"⚠️  Risk level: {analysis['risk_assessment']['risk_level']}")
        print(f"💱 Currency impact: {analysis['currency_analysis']['equity_impact']}")
        print(f"📈 Technical bias: {analysis['technical_signals']['market_bias']}")
        
        # Display recommendations
        recommendations = analysis['trading_recommendations']
        print(f"\n💡 Trading Recommendations:")
        print(f"   Position sizing: {recommendations['position_sizing']}")
        print(f"   Strategy preference: {recommendations['strategy_preference']}")
        print(f"   Risk management: {recommendations['risk_management']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pre-market intelligence test failed: {e}")
        return False

def test_enhanced_morning_validation():
    """Test enhanced morning validation"""
    print("\n🌅 Testing Enhanced Morning Validation")
    print("=" * 50)
    
    try:
        # Initialize enhanced validation
        validator = EnhancedMorningValidation()
        
        print("🔍 Running comprehensive morning analysis...")
        result = validator.comprehensive_morning_analysis()
        
        print("✅ Enhanced morning validation completed!")
        print(f"🎯 Confidence score: {result['confidence_score']:.2f}")
        print(f"✅ Trading ready: {result['trading_ready']}")
        print(f"⏱️  Validation duration: {result['validation_duration']:.1f} seconds")
        
        # Display key insights
        intelligence = result['intelligence_report']
        print(f"\n📊 Key Insights:")
        print(f"   News sentiment: {intelligence['news_sentiment']['sentiment_category']}")
        print(f"   Global bias: {intelligence['global_markets']['global_bias']}")
        print(f"   Risk assessment: {intelligence['risk_assessment']['risk_level']}")
        
        recommendations = result['enhanced_recommendations']
        print(f"\n💡 Enhanced Recommendations:")
        print(f"   Position sizing: {recommendations['position_sizing']}")
        print(f"   Strategy selection: {recommendations['strategy_selection']}")
        print(f"   Risk management: {recommendations['risk_management']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced morning validation test failed: {e}")
        return False

def create_sample_premarket_report():
    """Create a sample pre-market report"""
    print("\n📋 Creating Sample Pre-Market Report")
    print("=" * 50)
    
    try:
        intelligence = PreMarketIntelligenceSystem()
        analysis = intelligence.get_comprehensive_premarket_analysis()
        
        # Create formatted report
        report = f"""
🌅 PRE-MARKET INTELLIGENCE REPORT
Date: {analysis['timestamp'][:10]}
Time: {analysis['timestamp'][11:19]}

📰 NEWS SENTIMENT ANALYSIS
├─ Overall Sentiment: {analysis['news_sentiment']['sentiment_category']}
├─ Sentiment Score: {analysis['news_sentiment']['overall_sentiment']:.3f}
├─ Total News Items: {analysis['news_sentiment']['total_news_items']}
└─ Key Topics: {', '.join(analysis['news_sentiment']['key_topics'])}

🌍 GLOBAL MARKET CONDITIONS
├─ Global Bias: {analysis['global_markets']['global_bias']}
├─ Average Change: {analysis['global_markets']['average_change']:.2f}%
├─ Volatility: {analysis['global_markets']['volatility']:.2f}%
└─ Risk-On Sentiment: {'Yes' if analysis['global_markets']['risk_on_sentiment'] else 'No'}

⚠️  RISK ASSESSMENT
├─ Risk Level: {analysis['risk_assessment']['risk_level']}
├─ Risk Score: {analysis['risk_assessment']['risk_score']}/100
├─ Risk Factors: {len(analysis['risk_assessment']['risk_factors'])} identified
└─ Recommendation: {analysis['risk_assessment']['recommendation']}

💱 CURRENCY ANALYSIS
├─ USD-INR Rate: ₹{analysis['currency_analysis']['usd_inr_rate']:.2f}
├─ USD Change: {analysis['currency_analysis']['usd_change_percent']:.2f}%
└─ Equity Impact: {analysis['currency_analysis']['equity_impact']}

📈 TECHNICAL SIGNALS
├─ Market Bias: {analysis['technical_signals']['market_bias']}
└─ Bullish Ratio: {analysis['technical_signals']['bullish_ratio']:.1%}

💡 TRADING RECOMMENDATIONS
├─ Position Sizing: {analysis['trading_recommendations']['position_sizing']}
├─ Strategy Preference: {analysis['trading_recommendations']['strategy_preference']}
└─ Risk Management: {analysis['trading_recommendations']['risk_management']}

🎯 SPECIFIC ACTIONS:
"""
        
        for action in analysis['trading_recommendations']['specific_actions']:
            report += f"   • {action}\n"
        
        # Save report
        with open('sample_premarket_report.txt', 'w') as f:
            f.write(report)
        
        print("✅ Sample pre-market report created!")
        print("📁 Saved as: sample_premarket_report.txt")
        
        # Display first part of report
        print("\n📋 Report Preview:")
        print(report[:800] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample report: {e}")
        return False

def main():
    """Main testing function"""
    print("🧪 PRE-MARKET INTELLIGENCE SYSTEM TESTING")
    print("=" * 60)
    
    results = []
    
    # Test 1: Basic pre-market intelligence
    results.append(test_premarket_intelligence())
    
    # Test 2: Enhanced morning validation
    results.append(test_enhanced_morning_validation())
    
    # Test 3: Sample report generation
    results.append(create_sample_premarket_report())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Pre-market intelligence system is ready!")
        print("\n📝 Next Steps:")
        print("   1. Review sample_premarket_report.txt")
        print("   2. Check enhanced_morning_validation.json")
        print("   3. Integrate with morning automation")
        print("   4. Set up news source API keys for production")
        
    elif passed >= 2:
        print("✅ Core functionality working!")
        print("⚠️  Some features may need configuration")
        
    else:
        print("⚠️  Multiple issues detected")
        print("📝 Check error messages above")
    
    return passed >= 2

if __name__ == "__main__":
    main()
