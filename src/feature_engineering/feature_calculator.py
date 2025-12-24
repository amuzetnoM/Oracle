"""
Feature Calculator
Computes all technical indicators for a given dataset
"""

import numpy as np
from typing import Dict, List, Optional, Any
from src.logger import get_logger
from src.feature_engineering.indicators import MovingAverages, Momentum, Volatility, Volume


logger = get_logger(__name__)


class FeatureCalculator:
    """
    Calculate technical indicators from OHLCV data.
    All calculations use pure numpy - no ML frameworks.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize feature calculator.
        
        Args:
            config: Optional configuration for indicator parameters
        """
        self.logger = get_logger(__name__)
        self.config = config or {}
        
        # Default indicator parameters
        self.params = {
            'sma_periods': [10, 20, 50, 200],
            'ema_periods': [12, 26],
            'rsi_period': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'bb_period': 20,
            'bb_std': 2.0,
            'atr_period': 14,
            'obv_enabled': True,
            'vwap_enabled': True
        }
        
        # Override with custom config
        if config:
            self.params.update(config)
    
    def calculate_all(self, data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Calculate all configured indicators.
        
        Args:
            data: Dictionary with keys: open, high, low, close, volume
            
        Returns:
            Dictionary with all calculated features
        """
        if not self._validate_data(data):
            self.logger.error("Invalid data format")
            return {}
        
        features = {}
        
        # Add moving averages
        features.update(self._calculate_moving_averages(data['close']))
        
        # Add momentum indicators
        features.update(self._calculate_momentum(data))
        
        # Add volatility indicators
        features.update(self._calculate_volatility(data))
        
        # Add volume indicators
        features.update(self._calculate_volume(data))
        
        self.logger.info(f"Calculated {len(features)} features")
        return features
    
    def _validate_data(self, data: Dict[str, np.ndarray]) -> bool:
        """Validate input data format."""
        required = ['open', 'high', 'low', 'close', 'volume']
        
        for key in required:
            if key not in data:
                self.logger.error(f"Missing required field: {key}")
                return False
            
            if not isinstance(data[key], np.ndarray):
                self.logger.error(f"Field {key} must be numpy array")
                return False
        
        # Check all arrays have same length
        lengths = [len(data[key]) for key in required]
        if len(set(lengths)) > 1:
            self.logger.error("All arrays must have same length")
            return False
        
        return True
    
    def _calculate_moving_averages(self, close: np.ndarray) -> Dict[str, np.ndarray]:
        """Calculate moving average indicators."""
        features = {}
        
        # SMA for various periods
        for period in self.params.get('sma_periods', []):
            features[f'sma_{period}'] = MovingAverages.simple(close, period)
        
        # EMA for various periods
        for period in self.params.get('ema_periods', []):
            features[f'ema_{period}'] = MovingAverages.exponential(close, period)
        
        return features
    
    def _calculate_momentum(self, data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Calculate momentum indicators."""
        features = {}
        close = data['close']
        high = data['high']
        low = data['low']
        
        # RSI
        rsi_period = self.params.get('rsi_period', 14)
        features['rsi'] = Momentum.rsi(close, rsi_period)
        
        # MACD
        macd_fast = self.params.get('macd_fast', 12)
        macd_slow = self.params.get('macd_slow', 26)
        macd_signal = self.params.get('macd_signal', 9)
        macd_line, signal_line, histogram = Momentum.macd(close, macd_fast, macd_slow, macd_signal)
        features['macd'] = macd_line
        features['macd_signal'] = signal_line
        features['macd_histogram'] = histogram
        
        # Stochastic
        stoch_k, stoch_d = Momentum.stochastic(high, low, close, 14)
        features['stoch_k'] = stoch_k
        features['stoch_d'] = stoch_d
        
        # Rate of Change
        features['roc'] = Momentum.roc(close, 10)
        
        # Williams %R
        features['williams_r'] = Momentum.williams_r(high, low, close, 14)
        
        return features
    
    def _calculate_volatility(self, data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Calculate volatility indicators."""
        features = {}
        close = data['close']
        high = data['high']
        low = data['low']
        
        # ATR
        atr_period = self.params.get('atr_period', 14)
        features['atr'] = Volatility.atr(high, low, close, atr_period)
        
        # Bollinger Bands
        bb_period = self.params.get('bb_period', 20)
        bb_std = self.params.get('bb_std', 2.0)
        bb_upper, bb_middle, bb_lower = Volatility.bollinger_bands(close, bb_period, bb_std)
        features['bb_upper'] = bb_upper
        features['bb_middle'] = bb_middle
        features['bb_lower'] = bb_lower
        features['bb_width'] = (bb_upper - bb_lower) / (bb_middle + 1e-10)  # Normalized width
        
        # Standard Deviation
        features['std_dev'] = Volatility.std_dev(close, 20)
        
        # Historical Volatility
        features['hist_vol'] = Volatility.historical_vol(close, 20)
        
        return features
    
    def _calculate_volume(self, data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Calculate volume indicators."""
        features = {}
        close = data['close']
        high = data['high']
        low = data['low']
        volume = data['volume']
        
        if not self.params.get('obv_enabled', True):
            return features
        
        # On-Balance Volume
        features['obv'] = Volume.obv(close, volume)
        
        # VWAP
        if self.params.get('vwap_enabled', True):
            features['vwap'] = Volume.vwap(high, low, close, volume)
        
        # Volume Rate of Change
        features['vroc'] = Volume.vroc(volume, 10)
        
        # Accumulation/Distribution Line
        features['ad_line'] = Volume.ad_line(high, low, close, volume)
        
        # Chaikin Money Flow
        features['cmf'] = Volume.cmf(high, low, close, volume, 20)
        
        return features
    
    def get_feature_names(self) -> List[str]:
        """
        Get list of all feature names that will be calculated.
        
        Returns:
            List of feature names
        """
        # This is a static list based on current configuration
        features = []
        
        # Moving averages
        for period in self.params.get('sma_periods', []):
            features.append(f'sma_{period}')
        for period in self.params.get('ema_periods', []):
            features.append(f'ema_{period}')
        
        # Momentum
        features.extend(['rsi', 'macd', 'macd_signal', 'macd_histogram',
                        'stoch_k', 'stoch_d', 'roc', 'williams_r'])
        
        # Volatility
        features.extend(['atr', 'bb_upper', 'bb_middle', 'bb_lower', 'bb_width',
                        'std_dev', 'hist_vol'])
        
        # Volume
        if self.params.get('obv_enabled', True):
            features.extend(['obv', 'vwap', 'vroc', 'ad_line', 'cmf'])
        
        return features
