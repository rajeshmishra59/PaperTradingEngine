#!/bin/bash
# ENHANCED MORNING VALIDATION WITH PRE-MARKET INTELLIGENCE
# Updated morning automation script that includes comprehensive pre-market analysis

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="logs/morning_validation/$(date +%Y-%m-%d).log"

echo "🌅 Starting Enhanced Morning Validation with Pre-Market Intelligence - $(date)" >> "$LOG_FILE"

# Step 1: Run pre-market intelligence analysis
echo "📊 Running pre-market intelligence analysis..." >> "$LOG_FILE"
python3 -c "
from premarket_intelligence import PreMarketIntelligenceSystem
intelligence = PreMarketIntelligenceSystem()
analysis = intelligence.get_comprehensive_premarket_analysis()
print('✅ Pre-market analysis completed')
print(f'News Sentiment: {analysis[\"news_sentiment\"][\"sentiment_category\"]}')
print(f'Global Bias: {analysis[\"global_markets\"][\"global_bias\"]}')
print(f'Risk Level: {analysis[\"risk_assessment\"][\"risk_level\"]}')
" >> "$LOG_FILE" 2>&1

# Step 2: Run enhanced morning validation
echo "🔍 Running enhanced morning validation..." >> "$LOG_FILE"
python3 enhanced_morning_validation.py >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Enhanced morning validation completed - $(date)" >> "$LOG_FILE"
    
    # Step 3: Check trading readiness
    TRADING_READY=$(python3 -c "
import json
try:
    with open('enhanced_morning_validation.json', 'r') as f:
        result = json.load(f)
    print(result.get('trading_ready', False))
except:
    print(False)
")
    
    if [ "$TRADING_READY" = "True" ]; then
        echo "✅ System ready for trading - $(date)" >> "$LOG_FILE"
        
        # Step 4: Generate pre-market summary
        echo "📋 Generating pre-market summary..." >> "$LOG_FILE"
        python3 -c "
import json
try:
    with open('enhanced_morning_validation.json', 'r') as f:
        result = json.load(f)
    
    intel = result['intelligence_report']
    recommendations = result['enhanced_recommendations']
    
    print('📊 PRE-MARKET SUMMARY:')
    print(f'   News Sentiment: {intel[\"news_sentiment\"][\"sentiment_category\"]}')
    print(f'   Global Markets: {intel[\"global_markets\"][\"global_bias\"]}')
    print(f'   Risk Level: {intel[\"risk_assessment\"][\"risk_level\"]}')
    print(f'   Position Sizing: {recommendations[\"position_sizing\"]}')
    print(f'   Strategy: {recommendations[\"strategy_selection\"]}')
    print(f'   Risk Management: {recommendations[\"risk_management\"]}')
    print(f'   Confidence: {result[\"confidence_score\"]:.2f}')
except Exception as e:
    print(f'Error generating summary: {e}')
" >> "$LOG_FILE" 2>&1
        
        # Step 5: Start paper trading with enhanced parameters
        echo "🚀 Starting Paper Trading with Enhanced Parameters - $(date)" >> "$LOG_FILE"
        nohup python3 main_papertrader.py >> logs/morning_validation/papertrading_$(date +%Y-%m-%d).log 2>&1 &
        
        echo "📈 Paper trading started with pre-market intelligence - $(date)" >> "$LOG_FILE"
        
        # Step 6: Send notification (if configured)
        echo "📱 Sending trading start notification..." >> "$LOG_FILE"
        python3 -c "
print('📱 TRADING STARTED - $(date +%H:%M)')
print('✅ Pre-market analysis complete')
print('✅ Parameters validated and adjusted')
print('✅ Paper trading active')
print('📊 Check logs for detailed analysis')
" >> "$LOG_FILE" 2>&1
        
    else
        echo "❌ System not ready for trading - validation failed" >> "$LOG_FILE"
        echo "⚠️ Paper trading NOT started due to validation failure" >> "$LOG_FILE"
        
        # Generate failure report
        python3 -c "
try:
    with open('enhanced_morning_validation.json', 'r') as f:
        result = json.load(f)
    
    print('❌ VALIDATION FAILURE REPORT:')
    print(f'   Confidence Score: {result.get(\"confidence_score\", 0):.2f}')
    
    intel = result.get('intelligence_report', {})
    risk = intel.get('risk_assessment', {})
    
    if risk.get('risk_level') == 'HIGH':
        print(f'   High Risk Detected: {risk.get(\"risk_score\", 0)}/100')
        print(f'   Risk Factors: {len(risk.get(\"risk_factors\", []))} identified')
    
    print('   Manual review required before trading')
    
except Exception as e:
    print(f'Error generating failure report: {e}')
" >> "$LOG_FILE" 2>&1
    fi
    
else
    echo "❌ Enhanced morning validation failed - $(date)" >> "$LOG_FILE"
    echo "⚠️ Paper trading NOT started due to validation failure" >> "$LOG_FILE"
    
    # Fallback to basic validation
    echo "🔄 Attempting fallback to basic validation..." >> "$LOG_FILE"
    python3 hybrid_optimization_system.py --mode morning >> "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "✅ Fallback validation successful - starting conservative trading" >> "$LOG_FILE"
        nohup python3 main_papertrader.py >> logs/morning_validation/papertrading_$(date +%Y-%m-%d).log 2>&1 &
    else
        echo "❌ All validation methods failed - trading suspended" >> "$LOG_FILE"
    fi
fi

echo "📊 Enhanced morning validation process completed - $(date)" >> "$LOG_FILE"
