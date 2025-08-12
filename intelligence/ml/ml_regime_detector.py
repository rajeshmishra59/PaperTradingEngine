"""
MACHINE LEARNING REGIME DETECTOR
Statistical and ML-based market regime detection using:
1. Hidden Markov Models (HMM)
2. K-means Clustering
3. Statistical Feature Engineering
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from hmmlearn import hmm
import talib
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class MLRegimeDetector:
    """
    Advanced Machine Learning based Market Regime Detection
    Combines statistical methods with unsupervised learning
    """
    
    def __init__(self, n_regimes: int = 4, lookback_period: int = 100):
        self.n_regimes = n_regimes
        self.lookback_period = lookback_period
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=n_regimes, random_state=42)
        self.hmm_model = hmm.GaussianHMM(n_components=n_regimes, random_state=42)
        self.pca = PCA(n_components=0.95)  # Keep 95% variance
        
        # Feature importance tracking
        self.feature_importance = {}
        self.regime_characteristics = {}
        
    def engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Comprehensive feature engineering for regime detection
        Creates statistical and technical features
        """
        df = data.copy()
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        
        features = pd.DataFrame(index=df.index)
        
        # --- PRICE-BASED FEATURES ---
        # Returns and volatility
        features['returns'] = close.pct_change()
        features['log_returns'] = np.log(close / close.shift(1))
        features['volatility'] = features['returns'].rolling(20).std()
        features['realized_vol'] = features['returns'].rolling(5).std() * np.sqrt(252)
        
        # Price momentum features
        for period in [5, 10, 20, 50]:
            features[f'momentum_{period}'] = close / close.shift(period) - 1
            features[f'price_ma_ratio_{period}'] = close / talib.SMA(close, timeperiod=period)
        
        # --- TECHNICAL INDICATORS ---
        # Trend indicators
        features['rsi'] = talib.RSI(close, timeperiod=14)
        features['macd'], features['macd_signal'], features['macd_hist'] = talib.MACD(close)
        features['adx'] = talib.ADX(high, low, close, timeperiod=14)
        features['cci'] = talib.CCI(high, low, close, timeperiod=20)
        
        # Volatility indicators
        features['atr'] = talib.ATR(high, low, close, timeperiod=14)
        features['atr_ratio'] = features['atr'] / close
        bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=20)
        features['bb_width'] = (bb_upper - bb_lower) / bb_middle
        features['bb_position'] = (close - bb_lower) / (bb_upper - bb_lower)
        
        # --- VOLUME FEATURES ---
        features['volume_sma'] = talib.SMA(volume, timeperiod=20)
        features['volume_ratio'] = volume / features['volume_sma']
        features['vwap'] = (close * volume).cumsum() / volume.cumsum()
        features['price_vwap_ratio'] = close / features['vwap']
        
        # --- MICROSTRUCTURE FEATURES ---
        # High-Low analysis
        features['hl_ratio'] = (high - low) / close
        features['close_position'] = (close - low) / (high - low)
        
        # Gap analysis
        features['gap'] = (close - close.shift(1)) / close.shift(1)
        features['gap_abs'] = np.abs(features['gap'])
        
        # --- STATISTICAL FEATURES ---
        # Rolling statistics
        for window in [10, 20, 50]:
            features[f'skew_{window}'] = features['returns'].rolling(window).skew()
            features[f'kurt_{window}'] = features['returns'].rolling(window).kurtosis()
            features[f'sharpe_{window}'] = features['returns'].rolling(window).mean() / features['returns'].rolling(window).std()
        
        # Autocorrelation features
        for lag in [1, 2, 5]:
            features[f'autocorr_{lag}'] = features['returns'].rolling(50).apply(
                lambda x: x.autocorr(lag=lag), raw=False
            )
        
        # --- REGIME-SPECIFIC FEATURES ---
        # Trend strength
        features['trend_strength'] = np.abs(features['momentum_20'])
        
        # Range-bound indicator
        features['range_factor'] = features['bb_width'] / features['bb_width'].rolling(50).mean()
        
        # Volatility clustering
        features['vol_cluster'] = features['volatility'] / features['volatility'].rolling(50).mean()
        
        # Market stress indicator
        features['stress_indicator'] = (
            features['volatility'] * features['volume_ratio'] * features['gap_abs']
        )
        
        return features.dropna()
    
    def extract_regime_features(self, features: pd.DataFrame) -> np.ndarray:
        """
        Select and prepare features for regime detection
        Focus on most informative features
        """
        # Key features for regime detection
        regime_features = [
            'volatility', 'realized_vol', 'trend_strength', 'range_factor',
            'vol_cluster', 'stress_indicator', 'momentum_20', 'adx',
            'bb_width', 'volume_ratio', 'rsi', 'atr_ratio'
        ]
        
        # Add available features
        available_features = [f for f in regime_features if f in features.columns]
        feature_matrix = features[available_features].values
        
        # Handle NaN values
        feature_matrix = np.nan_to_num(feature_matrix, nan=0.0)
        
        return feature_matrix
    
    def fit_kmeans_regimes(self, feature_matrix: np.ndarray) -> np.ndarray:
        """
        K-means clustering for regime detection
        """
        # Standardize features
        scaled_features = self.scaler.fit_transform(feature_matrix)
        
        # Apply PCA for dimensionality reduction
        pca_features = self.pca.fit_transform(scaled_features)
        
        # Fit K-means
        regime_labels = self.kmeans.fit_predict(pca_features)
        
        # Analyze regime characteristics
        self._analyze_regime_characteristics(feature_matrix, regime_labels)
        
        return regime_labels
    
    def fit_hmm_regimes(self, feature_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Hidden Markov Model for regime detection
        Captures temporal dependencies
        """
        # Prepare features for HMM
        scaled_features = self.scaler.fit_transform(feature_matrix)
        
        # Fit HMM model
        self.hmm_model.fit(scaled_features)
        
        # Predict regimes and probabilities
        regime_labels = self.hmm_model.predict(scaled_features)
        regime_probs = self.hmm_model.predict_proba(scaled_features)
        
        return regime_labels, regime_probs
    
    def _analyze_regime_characteristics(self, feature_matrix: np.ndarray, regime_labels: np.ndarray):
        """
        Analyze characteristics of each detected regime
        """
        feature_names = [
            'volatility', 'realized_vol', 'trend_strength', 'range_factor',
            'vol_cluster', 'stress_indicator', 'momentum_20', 'adx',
            'bb_width', 'volume_ratio', 'rsi', 'atr_ratio'
        ]
        
        for regime in range(self.n_regimes):
            regime_mask = regime_labels == regime
            regime_data = feature_matrix[regime_mask]
            
            if len(regime_data) > 0:
                characteristics = {}
                for i, feature_name in enumerate(feature_names):
                    if i < regime_data.shape[1]:
                        characteristics[feature_name] = {
                            'mean': np.mean(regime_data[:, i]),
                            'std': np.std(regime_data[:, i]),
                            'percentile_25': np.percentile(regime_data[:, i], 25),
                            'percentile_75': np.percentile(regime_data[:, i], 75)
                        }
                
                self.regime_characteristics[regime] = characteristics
    
    def detect_current_regime(self, data: pd.DataFrame) -> Dict:
        """
        Detect current market regime using both methods
        """
        # Engineer features
        features = self.engineer_features(data)
        
        if len(features) < self.lookback_period:
            return {
                'kmeans_regime': 0,
                'hmm_regime': 0,
                'hmm_probabilities': [0.25] * 4,
                'confidence': 0.0,
                'method': 'insufficient_data'
            }
        
        # Extract recent features
        recent_features = features.tail(self.lookback_period)
        feature_matrix = self.extract_regime_features(recent_features)
        
        # K-means regime detection
        kmeans_regimes = self.fit_kmeans_regimes(feature_matrix)
        current_kmeans_regime = kmeans_regimes[-1]
        
        # HMM regime detection
        hmm_regimes, hmm_probs = self.fit_hmm_regimes(feature_matrix)
        current_hmm_regime = hmm_regimes[-1]
        current_hmm_probs = hmm_probs[-1]
        
        # Calculate confidence based on probability concentration
        confidence = np.max(current_hmm_probs)
        
        # Consensus method
        if current_kmeans_regime == current_hmm_regime:
            consensus_regime = current_kmeans_regime
            consensus_confidence = min(confidence * 1.2, 1.0)
        else:
            # Use HMM result with lower confidence
            consensus_regime = current_hmm_regime
            consensus_confidence = confidence * 0.8
        
        return {
            'kmeans_regime': int(current_kmeans_regime),
            'hmm_regime': int(current_hmm_regime),
            'consensus_regime': int(consensus_regime),
            'hmm_probabilities': current_hmm_probs.tolist(),
            'confidence': float(consensus_confidence),
            'method': 'ml_consensus',
            'regime_characteristics': self.regime_characteristics.get(consensus_regime, {})
        }
    
    def get_regime_interpretation(self, regime_id: int) -> str:
        """
        Interpret regime based on characteristics
        """
        if regime_id not in self.regime_characteristics:
            return "Unknown Regime"
        
        chars = self.regime_characteristics[regime_id]
        
        # Analyze key characteristics
        volatility = chars.get('volatility', {}).get('mean', 0)
        trend_strength = chars.get('trend_strength', {}).get('mean', 0)
        range_factor = chars.get('range_factor', {}).get('mean', 1)
        
        if volatility > 0.02 and trend_strength > 0.05:
            return "High Volatility Trending"
        elif volatility < 0.01 and range_factor < 0.8:
            return "Low Volatility Range-Bound"
        elif trend_strength > 0.03:
            return "Strong Trending"
        elif range_factor < 0.9:
            return "Range-Bound Consolidation"
        else:
            return f"Mixed Regime {regime_id}"

class StatisticalRegimeDetector:
    """
    Statistical methods for regime detection
    Based on structural breaks and change point detection
    """
    
    def __init__(self, window_size: int = 50):
        self.window_size = window_size
    
    def rolling_correlation_regime(self, data: pd.DataFrame, market_index: pd.Series = None) -> np.ndarray:
        """
        Detect regimes based on rolling correlation with market
        """
        returns = data['close'].pct_change()
        
        if market_index is not None:
            market_returns = market_index.pct_change()
            rolling_corr = returns.rolling(self.window_size).corr(market_returns)
        else:
            # Use autocorrelation as proxy
            rolling_corr = returns.rolling(self.window_size).apply(
                lambda x: x.autocorr(lag=1), raw=False
            )
        
        # Classify based on correlation levels
        regimes = np.zeros(len(rolling_corr))
        regimes[rolling_corr > 0.7] = 0  # High correlation regime
        regimes[(rolling_corr > 0.3) & (rolling_corr <= 0.7)] = 1  # Medium correlation
        regimes[(rolling_corr > -0.3) & (rolling_corr <= 0.3)] = 2  # Low correlation
        regimes[rolling_corr <= -0.3] = 3  # Negative correlation
        
        return regimes
    
    def variance_change_point_detection(self, data: pd.DataFrame) -> List[int]:
        """
        Detect change points in variance (regime changes)
        """
        returns = data['close'].pct_change().dropna()
        squared_returns = returns ** 2
        
        change_points = []
        window = self.window_size
        
        for i in range(window, len(squared_returns) - window):
            # Test for variance change
            before_var = squared_returns.iloc[i-window:i].var()
            after_var = squared_returns.iloc[i:i+window].var()
            
            # F-test for variance equality
            f_stat = max(before_var, after_var) / min(before_var, after_var)
            
            # Simple threshold (can be made more sophisticated)
            if f_stat > 2.0:  # Significant variance change
                change_points.append(i)
        
        return change_points

if __name__ == "__main__":
    print("🧠 MACHINE LEARNING REGIME DETECTOR")
    print("✅ Hidden Markov Models")
    print("✅ K-means Clustering")
    print("✅ Statistical Feature Engineering") 
    print("✅ Change Point Detection")
    print("✅ Multi-method Consensus")
    print("\nAdvanced regime detection ready!")
