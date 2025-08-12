"""
PRE-MARKET INTELLIGENCE SYSTEM
Real-time news, sentiment, and market condition analysis before market open
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import re
from typing import Dict, List, Tuple, Optional
import logging
from textblob import TextBlob
import yfinance as yf
from bs4 import BeautifulSoup
import feedparser

logger = logging.getLogger(__name__)

class PreMarketIntelligenceSystem:
    """
    Comprehensive pre-market analysis system covering:
    1. News sentiment analysis
    2. Global market conditions
    3. Economic indicators
    4. Corporate announcements
    5. Technical pre-market signals
    """
    
    def __init__(self):
        self.news_sources = {
            'economic_times': 'https://economictimes.indiatimes.com/markets/rss/markets',
            'moneycontrol': 'https://www.moneycontrol.com/rss/marketstories.xml',
            'business_standard': 'https://www.business-standard.com/rss/markets-106.rss',
            'livemint': 'https://www.livemint.com/rss/markets',
            'reuters_india': 'https://feeds.reuters.com/reuters/INbusinessNews'
        }
        
        self.global_indices = {
            'dow_jones': '^DJI',
            'nasdaq': '^IXIC',
            'sp500': '^GSPC',
            'nikkei': '^N225',
            'hang_seng': '^HSI',
            'ftse': '^FTSE',
            'dax': '^GDAXI'
        }
        
        self.key_symbols = [
            'NIFTY50.NS', 'BANKNIFTY.NS', 'RELIANCE.NS', 'TCS.NS', 'INFY.NS'
        ]
        
    def get_comprehensive_premarket_analysis(self) -> Dict:
        """
        Get complete pre-market intelligence report
        """
        logger.info("🌅 Starting Pre-Market Intelligence Analysis")
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'news_sentiment': self.analyze_news_sentiment(),
            'global_markets': self.analyze_global_markets(),
            'economic_indicators': self.get_economic_indicators(),
            'corporate_announcements': self.scan_corporate_announcements(),
            'technical_signals': self.analyze_premarket_technicals(),
            'currency_analysis': self.analyze_currency_impact(),
            'risk_assessment': {},
            'trading_recommendations': {}
        }
        
        # Generate risk assessment
        analysis['risk_assessment'] = self.generate_risk_assessment(analysis)
        
        # Generate trading recommendations
        analysis['trading_recommendations'] = self.generate_trading_recommendations(analysis)
        
        return analysis
    
    def analyze_news_sentiment(self) -> Dict:
        """
        Analyze news sentiment from multiple sources
        """
        logger.info("📰 Analyzing news sentiment...")
        
        all_news = []
        sentiment_scores = []
        
        for source, url in self.news_sources.items():
            try:
                news_items = self.fetch_news_from_rss(url, source)
                all_news.extend(news_items)
                
                for item in news_items:
                    sentiment = self.analyze_text_sentiment(item['title'] + ' ' + item.get('summary', ''))
                    sentiment_scores.append(sentiment)
                    
            except Exception as e:
                logger.warning(f"Failed to fetch news from {source}: {e}")
        
        # Overall sentiment calculation
        if sentiment_scores:
            avg_sentiment = np.mean(sentiment_scores)
            sentiment_std = np.std(sentiment_scores)
        else:
            avg_sentiment = 0
            sentiment_std = 0
        
        # Categorize sentiment
        if avg_sentiment > 0.1:
            sentiment_category = "POSITIVE"
        elif avg_sentiment < -0.1:
            sentiment_category = "NEGATIVE"
        else:
            sentiment_category = "NEUTRAL"
        
        # Key news topics
        key_topics = self.extract_key_topics(all_news)
        
        return {
            'overall_sentiment': float(avg_sentiment),
            'sentiment_category': sentiment_category,
            'sentiment_volatility': float(sentiment_std),
            'total_news_items': len(all_news),
            'key_topics': key_topics,
            'news_summary': all_news[:10],  # Top 10 news items
            'sentiment_distribution': {
                'positive': len([s for s in sentiment_scores if s > 0.1]),
                'negative': len([s for s in sentiment_scores if s < -0.1]),
                'neutral': len([s for s in sentiment_scores if -0.1 <= s <= 0.1])
            }
        }
    
    def analyze_global_markets(self) -> Dict:
        """
        Analyze global market performance impact
        """
        logger.info("🌍 Analyzing global markets...")
        
        global_data = {}
        
        for market, symbol in self.global_indices.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                
                if len(hist) >= 2:
                    current_close = hist['Close'].iloc[-1]
                    previous_close = hist['Close'].iloc[-2]
                    change_pct = ((current_close - previous_close) / previous_close) * 100
                    
                    global_data[market] = {
                        'current_price': float(current_close),
                        'previous_close': float(previous_close),
                        'change_percent': float(change_pct),
                        'volume': float(hist['Volume'].iloc[-1]) if 'Volume' in hist else 0
                    }
                    
            except Exception as e:
                logger.warning(f"Failed to get data for {market}: {e}")
        
        # Calculate global sentiment
        changes = [data['change_percent'] for data in global_data.values()]
        if changes:
            avg_global_change = np.mean(changes)
            global_volatility = np.std(changes)
        else:
            avg_global_change = 0
            global_volatility = 0
        
        # Determine global market bias
        if avg_global_change > 0.5:
            global_bias = "POSITIVE"
        elif avg_global_change < -0.5:
            global_bias = "NEGATIVE"
        else:
            global_bias = "NEUTRAL"
        
        return {
            'market_data': global_data,
            'global_bias': global_bias,
            'average_change': float(avg_global_change),
            'volatility': float(global_volatility),
            'risk_on_sentiment': avg_global_change > 0,
            'major_movers': self.identify_major_movers(global_data)
        }
    
    def get_economic_indicators(self) -> Dict:
        """
        Get important economic indicators and events
        """
        logger.info("📊 Checking economic indicators...")
        
        # This would integrate with economic calendar APIs
        # For now, using placeholder data
        
        indicators = {
            'upcoming_events': [
                {
                    'time': '10:00 AM',
                    'event': 'RBI Policy Decision',
                    'importance': 'HIGH',
                    'expected': 'No change in rates',
                    'previous': '6.50%'
                },
                {
                    'time': '2:00 PM',
                    'event': 'US Inflation Data',
                    'importance': 'MEDIUM',
                    'expected': '3.2%',
                    'previous': '3.0%'
                }
            ],
            'currency_impact': {
                'usd_inr': self.get_currency_data('USDINR=X'),
                'dxy_impact': 'moderate'
            },
            'commodity_watch': {
                'crude_oil': self.get_commodity_data('CL=F'),
                'gold': self.get_commodity_data('GC=F')
            }
        }
        
        return indicators
    
    def scan_corporate_announcements(self) -> Dict:
        """
        Scan for important corporate announcements
        """
        logger.info("🏢 Scanning corporate announcements...")
        
        # This would scan BSE/NSE announcements
        # For now, using mock data structure
        
        announcements = {
            'earnings_today': [
                {'company': 'RELIANCE', 'time': 'Post-market', 'consensus': 'Beat expected'},
                {'company': 'TCS', 'time': 'Pre-market', 'consensus': 'In-line'}
            ],
            'major_announcements': [
                {
                    'company': 'HDFCBANK',
                    'type': 'Merger Update',
                    'impact': 'POSITIVE',
                    'details': 'Integration ahead of schedule'
                }
            ],
            'dividend_announcements': [],
            'stock_splits': [],
            'insider_trading': []
        }
        
        return announcements
    
    def analyze_premarket_technicals(self) -> Dict:
        """
        Analyze pre-market technical indicators
        """
        logger.info("📈 Analyzing pre-market technicals...")
        
        technical_signals = {}
        
        for symbol in self.key_symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="10d", interval="1d")
                
                if len(hist) >= 5:
                    signals = self.calculate_technical_signals(hist)
                    technical_signals[symbol.replace('.NS', '')] = signals
                    
            except Exception as e:
                logger.warning(f"Failed to get technical data for {symbol}: {e}")
        
        # Overall market technical bias
        bullish_signals = sum(1 for signals in technical_signals.values() 
                            if signals.get('overall_bias') == 'BULLISH')
        
        total_signals = len(technical_signals)
        if total_signals > 0:
            bullish_ratio = bullish_signals / total_signals
        else:
            bullish_ratio = 0.5
        
        market_technical_bias = "BULLISH" if bullish_ratio > 0.6 else "BEARISH" if bullish_ratio < 0.4 else "NEUTRAL"
        
        return {
            'individual_signals': technical_signals,
            'market_bias': market_technical_bias,
            'bullish_ratio': float(bullish_ratio),
            'key_levels': self.identify_key_levels(technical_signals)
        }
    
    def analyze_currency_impact(self) -> Dict:
        """
        Analyze currency impact on Indian markets
        """
        logger.info("💱 Analyzing currency impact...")
        
        try:
            # USD-INR analysis
            usdinr = yf.Ticker('USDINR=X')
            usd_hist = usdinr.history(period="5d")
            
            if len(usd_hist) >= 2:
                current_rate = usd_hist['Close'].iloc[-1]
                previous_rate = usd_hist['Close'].iloc[-2]
                usd_change = ((current_rate - previous_rate) / previous_rate) * 100
            else:
                current_rate = 83.0  # Fallback
                usd_change = 0
            
            # Determine impact
            if usd_change > 0.5:
                impact = "NEGATIVE_FOR_EQUITY"  # Stronger USD = FII outflow
            elif usd_change < -0.5:
                impact = "POSITIVE_FOR_EQUITY"  # Weaker USD = FII inflow
            else:
                impact = "NEUTRAL"
            
            return {
                'usd_inr_rate': float(current_rate),
                'usd_change_percent': float(usd_change),
                'equity_impact': impact,
                'fii_flow_bias': "OUTFLOW" if usd_change > 0 else "INFLOW" if usd_change < 0 else "NEUTRAL"
            }
            
        except Exception as e:
            logger.warning(f"Currency analysis failed: {e}")
            return {'usd_inr_rate': 83.0, 'usd_change_percent': 0, 'equity_impact': 'NEUTRAL'}
    
    def generate_risk_assessment(self, analysis: Dict) -> Dict:
        """
        Generate overall risk assessment
        """
        risk_factors = []
        risk_score = 0  # 0-100 scale
        
        # News sentiment risk
        news_sentiment = analysis['news_sentiment']['overall_sentiment']
        if news_sentiment < -0.2:
            risk_factors.append("Negative news sentiment")
            risk_score += 20
        
        # Global market risk
        global_change = analysis['global_markets']['average_change']
        if global_change < -1.0:
            risk_factors.append("Weak global markets")
            risk_score += 25
        
        # Volatility risk
        global_vol = analysis['global_markets']['volatility']
        if global_vol > 2.0:
            risk_factors.append("High global volatility")
            risk_score += 15
        
        # Currency risk
        currency_impact = analysis['currency_analysis']['equity_impact']
        if currency_impact == "NEGATIVE_FOR_EQUITY":
            risk_factors.append("USD strength pressuring equities")
            risk_score += 10
        
        # Determine risk level
        if risk_score <= 20:
            risk_level = "LOW"
        elif risk_score <= 50:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        return {
            'risk_level': risk_level,
            'risk_score': min(risk_score, 100),
            'risk_factors': risk_factors,
            'recommendation': self.get_risk_recommendation(risk_level)
        }
    
    def generate_trading_recommendations(self, analysis: Dict) -> Dict:
        """
        Generate specific trading recommendations
        """
        recommendations = {
            'position_sizing': 'NORMAL',
            'strategy_preference': 'BALANCED',
            'risk_management': 'STANDARD',
            'sector_focus': [],
            'specific_actions': []
        }
        
        risk_level = analysis['risk_assessment']['risk_level']
        news_sentiment = analysis['news_sentiment']['sentiment_category']
        global_bias = analysis['global_markets']['global_bias']
        
        # Position sizing recommendation
        if risk_level == "HIGH":
            recommendations['position_sizing'] = 'REDUCE'
            recommendations['specific_actions'].append("Reduce position sizes by 30-50%")
        elif risk_level == "LOW" and news_sentiment == "POSITIVE" and global_bias == "POSITIVE":
            recommendations['position_sizing'] = 'INCREASE'
            recommendations['specific_actions'].append("Consider increasing position sizes by 20%")
        
        # Strategy preference
        if global_bias == "POSITIVE" and news_sentiment == "POSITIVE":
            recommendations['strategy_preference'] = 'TREND_FOLLOWING'
            recommendations['specific_actions'].append("Favor trend-following strategies")
        elif risk_level == "HIGH":
            recommendations['strategy_preference'] = 'CONSERVATIVE'
            recommendations['specific_actions'].append("Use conservative mean-reversion strategies")
        
        # Risk management adjustments
        if risk_level == "HIGH":
            recommendations['risk_management'] = 'TIGHT'
            recommendations['specific_actions'].append("Use tighter stop-losses (1.5x normal)")
        
        return recommendations
    
    # Helper methods
    def fetch_news_from_rss(self, url: str, source: str) -> List[Dict]:
        """Fetch news from RSS feed"""
        try:
            feed = feedparser.parse(url)
            news_items = []
            
            for entry in feed.entries[:10]:  # Latest 10 items
                item = {
                    'title': entry.title,
                    'summary': entry.get('summary', ''),
                    'link': entry.link,
                    'published': entry.get('published', ''),
                    'source': source
                }
                news_items.append(item)
            
            return news_items
        except:
            return []
    
    def analyze_text_sentiment(self, text: str) -> float:
        """Analyze sentiment of text"""
        try:
            blob = TextBlob(text)
            return blob.sentiment.polarity
        except:
            return 0.0
    
    def extract_key_topics(self, news_items: List[Dict]) -> List[str]:
        """Extract key topics from news"""
        # Simple keyword extraction
        keywords = ['market', 'economy', 'inflation', 'rate', 'earnings', 'merger', 'ipo']
        topics = []
        
        for item in news_items:
            text = (item['title'] + ' ' + item.get('summary', '')).lower()
            for keyword in keywords:
                if keyword in text and keyword not in topics:
                    topics.append(keyword)
        
        return topics[:5]  # Top 5 topics
    
    def identify_major_movers(self, global_data: Dict) -> List[Dict]:
        """Identify major market movers"""
        movers = []
        for market, data in global_data.items():
            if abs(data['change_percent']) > 1.0:
                movers.append({
                    'market': market,
                    'change': data['change_percent'],
                    'direction': 'UP' if data['change_percent'] > 0 else 'DOWN'
                })
        
        return sorted(movers, key=lambda x: abs(x['change']), reverse=True)
    
    def get_currency_data(self, symbol: str) -> Dict:
        """Get currency data"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                return {
                    'current': float(hist['Close'].iloc[-1]),
                    'change': float(((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100)
                }
        except:
            pass
        return {'current': 0, 'change': 0}
    
    def get_commodity_data(self, symbol: str) -> Dict:
        """Get commodity data"""
        return self.get_currency_data(symbol)  # Same structure
    
    def calculate_technical_signals(self, hist: pd.DataFrame) -> Dict:
        """Calculate technical signals"""
        close = hist['Close']
        
        # Simple moving averages
        sma_5 = close.rolling(5).mean().iloc[-1]
        sma_20 = close.rolling(20).mean().iloc[-1] if len(close) >= 20 else close.mean()
        current_price = close.iloc[-1]
        
        # Trend bias
        if current_price > sma_5 > sma_20:
            bias = "BULLISH"
        elif current_price < sma_5 < sma_20:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"
        
        return {
            'overall_bias': bias,
            'price_vs_sma5': float((current_price / sma_5 - 1) * 100),
            'price_vs_sma20': float((current_price / sma_20 - 1) * 100)
        }
    
    def identify_key_levels(self, technical_signals: Dict) -> Dict:
        """Identify key support/resistance levels"""
        # Simplified key levels
        return {
            'nifty_support': 19800,
            'nifty_resistance': 20200,
            'bank_nifty_support': 45000,
            'bank_nifty_resistance': 46500
        }
    
    def get_risk_recommendation(self, risk_level: str) -> str:
        """Get risk management recommendation"""
        recommendations = {
            'LOW': "Normal trading with standard risk management",
            'MEDIUM': "Moderate caution - reduce position sizes slightly",
            'HIGH': "High caution - significant position size reduction and tight stops"
        }
        return recommendations.get(risk_level, "Standard risk management")

if __name__ == "__main__":
    print("🌅 PRE-MARKET INTELLIGENCE SYSTEM")
    print("=" * 50)
    
    intelligence = PreMarketIntelligenceSystem()
    analysis = intelligence.get_comprehensive_premarket_analysis()
    
    print("📊 Analysis Complete!")
    print(f"Risk Level: {analysis['risk_assessment']['risk_level']}")
    print(f"Global Bias: {analysis['global_markets']['global_bias']}")
    print(f"News Sentiment: {analysis['news_sentiment']['sentiment_category']}")
    print(f"Position Sizing: {analysis['trading_recommendations']['position_sizing']}")
