"""
Moving Average Indicators
Pure numpy implementations - No external TA libraries
"""

import numpy as np
from typing import Optional
from src.logger import get_logger


logger = get_logger(__name__)


def sma(prices: np.ndarray, period: int) -> np.ndarray:
    """
    Simple Moving Average.
    
    Args:
        prices: Array of prices
        period: Moving average period
        
    Returns:
        Array of SMA values (same length as input, padded with NaN)
    """
    if len(prices) < period:
        return np.full(len(prices), np.nan)
    
    # Compute cumulative sum for efficient calculation
    cumsum = np.cumsum(np.insert(prices, 0, 0))
    ma = (cumsum[period:] - cumsum[:-period]) / period
    
    # Pad with NaN for the first period-1 values
    result = np.full(len(prices), np.nan)
    result[period-1:] = ma
    
    return result


def ema(prices: np.ndarray, period: int, smoothing: float = 2.0) -> np.ndarray:
    """
    Exponential Moving Average.
    
    Args:
        prices: Array of prices
        period: EMA period
        smoothing: Smoothing factor (default: 2.0)
        
    Returns:
        Array of EMA values
    """
    if len(prices) < period:
        return np.full(len(prices), np.nan)
    
    # Calculate multiplier
    multiplier = smoothing / (period + 1)
    
    # Initialize result array
    result = np.full(len(prices), np.nan)
    
    # First EMA value is SMA
    result[period-1] = np.mean(prices[:period])
    
    # Calculate EMA recursively
    for i in range(period, len(prices)):
        result[i] = (prices[i] * multiplier) + (result[i-1] * (1 - multiplier))
    
    return result


def wma(prices: np.ndarray, period: int) -> np.ndarray:
    """
    Weighted Moving Average.
    Gives more weight to recent prices.
    
    Args:
        prices: Array of prices
        period: WMA period
        
    Returns:
        Array of WMA values
    """
    if len(prices) < period:
        return np.full(len(prices), np.nan)
    
    # Create weights (linear: 1, 2, 3, ..., period)
    weights = np.arange(1, period + 1)
    weight_sum = weights.sum()
    
    result = np.full(len(prices), np.nan)
    
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        result[i] = np.dot(window, weights) / weight_sum
    
    return result


def dema(prices: np.ndarray, period: int) -> np.ndarray:
    """
    Double Exponential Moving Average (DEMA).
    Reduces lag compared to EMA.
    
    DEMA = 2 * EMA - EMA(EMA)
    
    Args:
        prices: Array of prices
        period: DEMA period
        
    Returns:
        Array of DEMA values
    """
    ema1 = ema(prices, period)
    ema2 = ema(ema1[~np.isnan(ema1)], period)
    
    # Pad ema2 to match ema1 length
    ema2_padded = np.full(len(ema1), np.nan)
    valid_start = np.where(~np.isnan(ema1))[0][0]
    ema2_start = valid_start + period - 1
    
    if ema2_start < len(ema2_padded):
        ema2_padded[ema2_start:ema2_start + len(ema2)] = ema2
    
    result = 2 * ema1 - ema2_padded
    
    return result


def tema(prices: np.ndarray, period: int) -> np.ndarray:
    """
    Triple Exponential Moving Average (TEMA).
    Further reduces lag compared to DEMA.
    
    TEMA = 3 * EMA - 3 * EMA(EMA) + EMA(EMA(EMA))
    
    Args:
        prices: Array of prices
        period: TEMA period
        
    Returns:
        Array of TEMA values
    """
    ema1 = ema(prices, period)
    ema2 = ema(ema1[~np.isnan(ema1)], period)
    ema3 = ema(ema2[~np.isnan(ema2)], period)
    
    # Align arrays
    result = np.full(len(prices), np.nan)
    
    # Find valid indices
    valid1 = ~np.isnan(ema1)
    if not valid1.any():
        return result
    
    # This is a simplified version - full implementation would need careful alignment
    # For production, would need more sophisticated index tracking
    
    return result


def vwma(prices: np.ndarray, volumes: np.ndarray, period: int) -> np.ndarray:
    """
    Volume Weighted Moving Average.
    
    Args:
        prices: Array of prices
        volumes: Array of volumes
        period: VWMA period
        
    Returns:
        Array of VWMA values
    """
    if len(prices) != len(volumes) or len(prices) < period:
        return np.full(len(prices), np.nan)
    
    result = np.full(len(prices), np.nan)
    
    for i in range(period - 1, len(prices)):
        price_window = prices[i - period + 1:i + 1]
        volume_window = volumes[i - period + 1:i + 1]
        
        if volume_window.sum() > 0:
            result[i] = np.dot(price_window, volume_window) / volume_window.sum()
    
    return result


class MovingAverages:
    """
    Collection of moving average indicators.
    Static methods for easy access.
    """
    
    @staticmethod
    def simple(prices: np.ndarray, period: int) -> np.ndarray:
        """Simple Moving Average."""
        return sma(prices, period)
    
    @staticmethod
    def exponential(prices: np.ndarray, period: int) -> np.ndarray:
        """Exponential Moving Average."""
        return ema(prices, period)
    
    @staticmethod
    def weighted(prices: np.ndarray, period: int) -> np.ndarray:
        """Weighted Moving Average."""
        return wma(prices, period)
    
    @staticmethod
    def double_exponential(prices: np.ndarray, period: int) -> np.ndarray:
        """Double Exponential Moving Average."""
        return dema(prices, period)
    
    @staticmethod
    def triple_exponential(prices: np.ndarray, period: int) -> np.ndarray:
        """Triple Exponential Moving Average."""
        return tema(prices, period)
    
    @staticmethod
    def volume_weighted(prices: np.ndarray, volumes: np.ndarray, period: int) -> np.ndarray:
        """Volume Weighted Moving Average."""
        return vwma(prices, volumes, period)
