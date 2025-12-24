"""
Momentum Indicators
RSI, MACD, Stochastic Oscillator - Pure numpy implementations
"""

import numpy as np
from typing import Tuple
from src.logger import get_logger
from src.feature_engineering.indicators.moving_averages import ema


logger = get_logger(__name__)


def rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Relative Strength Index (RSI).
    
    RSI = 100 - (100 / (1 + RS))
    where RS = Average Gain / Average Loss
    
    Args:
        prices: Array of prices
        period: RSI period (default: 14)
        
    Returns:
        Array of RSI values (0-100)
    """
    if len(prices) < period + 1:
        return np.full(len(prices), np.nan)
    
    # Calculate price changes
    deltas = np.diff(prices)
    
    # Separate gains and losses
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # Calculate average gains and losses
    avg_gains = np.full(len(prices), np.nan)
    avg_losses = np.full(len(prices), np.nan)
    
    # First average is simple mean
    avg_gains[period] = np.mean(gains[:period])
    avg_losses[period] = np.mean(losses[:period])
    
    # Subsequent values use smoothed average (Wilder's smoothing)
    for i in range(period + 1, len(prices)):
        avg_gains[i] = (avg_gains[i-1] * (period - 1) + gains[i-1]) / period
        avg_losses[i] = (avg_losses[i-1] * (period - 1) + losses[i-1]) / period
    
    # Calculate RS and RSI
    rs = avg_gains / (avg_losses + 1e-10)  # Add small epsilon to avoid division by zero
    rsi_values = 100 - (100 / (1 + rs))
    
    return rsi_values


def macd(
    prices: np.ndarray,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Moving Average Convergence Divergence (MACD).
    
    Args:
        prices: Array of prices
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line period (default: 9)
        
    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    if len(prices) < slow_period:
        return (
            np.full(len(prices), np.nan),
            np.full(len(prices), np.nan),
            np.full(len(prices), np.nan)
        )
    
    # Calculate fast and slow EMAs
    fast_ema = ema(prices, fast_period)
    slow_ema = ema(prices, slow_period)
    
    # MACD line = fast EMA - slow EMA
    macd_line = fast_ema - slow_ema
    
    # Signal line = EMA of MACD line
    # Need to remove NaN values for EMA calculation
    macd_valid = macd_line[~np.isnan(macd_line)]
    signal_line_values = ema(macd_valid, signal_period)
    
    # Pad signal line to match input length
    signal_line = np.full(len(prices), np.nan)
    signal_start = np.where(~np.isnan(macd_line))[0][0] + signal_period - 1
    if signal_start < len(signal_line):
        signal_line[signal_start:signal_start + len(signal_line_values)] = signal_line_values
    
    # Histogram = MACD line - Signal line
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def stochastic_oscillator(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = 14,
    smooth_k: int = 3,
    smooth_d: int = 3
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Stochastic Oscillator (%K and %D).
    
    %K = 100 * (Close - Lowest Low) / (Highest High - Lowest Low)
    %D = SMA of %K
    
    Args:
        high: Array of high prices
        low: Array of low prices
        close: Array of close prices
        period: Lookback period (default: 14)
        smooth_k: %K smoothing period (default: 3)
        smooth_d: %D smoothing period (default: 3)
        
    Returns:
        Tuple of (%K, %D) arrays
    """
    if len(high) < period or len(low) < period or len(close) < period:
        return (
            np.full(len(close), np.nan),
            np.full(len(close), np.nan)
        )
    
    # Initialize arrays
    k_fast = np.full(len(close), np.nan)
    
    # Calculate fast %K
    for i in range(period - 1, len(close)):
        window_high = high[i - period + 1:i + 1]
        window_low = low[i - period + 1:i + 1]
        
        highest_high = np.max(window_high)
        lowest_low = np.min(window_low)
        
        if highest_high - lowest_low != 0:
            k_fast[i] = 100 * (close[i] - lowest_low) / (highest_high - lowest_low)
        else:
            k_fast[i] = 50  # Neutral value when no range
    
    # Smooth %K (slow %K)
    k_slow = np.full(len(close), np.nan)
    for i in range(period + smooth_k - 2, len(close)):
        k_slow[i] = np.mean(k_fast[i - smooth_k + 1:i + 1])
    
    # Calculate %D (SMA of slow %K)
    d = np.full(len(close), np.nan)
    for i in range(period + smooth_k + smooth_d - 3, len(close)):
        d[i] = np.mean(k_slow[i - smooth_d + 1:i + 1])
    
    return k_slow, d


def momentum(prices: np.ndarray, period: int = 10) -> np.ndarray:
    """
    Momentum Indicator.
    
    Momentum = Current Price - Price N periods ago
    
    Args:
        prices: Array of prices
        period: Lookback period
        
    Returns:
        Array of momentum values
    """
    if len(prices) < period + 1:
        return np.full(len(prices), np.nan)
    
    result = np.full(len(prices), np.nan)
    result[period:] = prices[period:] - prices[:-period]
    
    return result


def rate_of_change(prices: np.ndarray, period: int = 10) -> np.ndarray:
    """
    Rate of Change (ROC).
    
    ROC = ((Current Price - Price N periods ago) / Price N periods ago) * 100
    
    Args:
        prices: Array of prices
        period: Lookback period
        
    Returns:
        Array of ROC values (percentage)
    """
    if len(prices) < period + 1:
        return np.full(len(prices), np.nan)
    
    result = np.full(len(prices), np.nan)
    result[period:] = ((prices[period:] - prices[:-period]) / (prices[:-period] + 1e-10)) * 100
    
    return result


def williams_r(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = 14
) -> np.ndarray:
    """
    Williams %R.
    
    %R = -100 * (Highest High - Close) / (Highest High - Lowest Low)
    
    Args:
        high: Array of high prices
        low: Array of low prices
        close: Array of close prices
        period: Lookback period (default: 14)
        
    Returns:
        Array of Williams %R values (-100 to 0)
    """
    if len(high) < period:
        return np.full(len(close), np.nan)
    
    result = np.full(len(close), np.nan)
    
    for i in range(period - 1, len(close)):
        highest_high = np.max(high[i - period + 1:i + 1])
        lowest_low = np.min(low[i - period + 1:i + 1])
        
        if highest_high - lowest_low != 0:
            result[i] = -100 * (highest_high - close[i]) / (highest_high - lowest_low)
        else:
            result[i] = -50
    
    return result


class Momentum:
    """
    Collection of momentum indicators.
    """
    
    @staticmethod
    def rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Relative Strength Index."""
        return rsi(prices, period)
    
    @staticmethod
    def macd(
        prices: np.ndarray,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Moving Average Convergence Divergence."""
        return macd(prices, fast, slow, signal)
    
    @staticmethod
    def stochastic(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Stochastic Oscillator."""
        return stochastic_oscillator(high, low, close, period)
    
    @staticmethod
    def momentum(prices: np.ndarray, period: int = 10) -> np.ndarray:
        """Simple Momentum."""
        return momentum(prices, period)
    
    @staticmethod
    def roc(prices: np.ndarray, period: int = 10) -> np.ndarray:
        """Rate of Change."""
        return rate_of_change(prices, period)
    
    @staticmethod
    def williams_r(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """Williams %R."""
        return williams_r(high, low, close, period)
