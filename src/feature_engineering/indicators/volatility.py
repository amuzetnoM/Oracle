"""
Volatility Indicators
ATR, Bollinger Bands, Standard Deviation - Pure numpy implementations
"""

import numpy as np
from typing import Tuple
from src.logger import get_logger
from src.feature_engineering.indicators.moving_averages import sma, ema


logger = get_logger(__name__)


def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Average True Range (ATR).
    Measures market volatility.
    
    True Range = max(high - low, abs(high - prev_close), abs(low - prev_close))
    ATR = EMA of True Range
    
    Args:
        high: Array of high prices
        low: Array of low prices
        close: Array of close prices
        period: ATR period (default: 14)
        
    Returns:
        Array of ATR values
    """
    if len(high) < period + 1:
        return np.full(len(close), np.nan)
    
    # Calculate True Range
    tr = np.full(len(close), np.nan)
    
    # First TR is just high - low
    tr[0] = high[0] - low[0]
    
    # Subsequent TRs consider previous close
    for i in range(1, len(close)):
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i-1])
        lc = abs(low[i] - close[i-1])
        tr[i] = max(hl, hc, lc)
    
    # ATR is smoothed average of TR (using Wilder's smoothing method)
    atr_values = np.full(len(close), np.nan)
    
    # First ATR is simple mean
    atr_values[period-1] = np.mean(tr[:period])
    
    # Subsequent values use smoothed average
    for i in range(period, len(close)):
        atr_values[i] = (atr_values[i-1] * (period - 1) + tr[i]) / period
    
    return atr_values


def bollinger_bands(
    prices: np.ndarray,
    period: int = 20,
    num_std: float = 2.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Bollinger Bands.
    
    Middle Band = SMA
    Upper Band = SMA + (num_std * std_dev)
    Lower Band = SMA - (num_std * std_dev)
    
    Args:
        prices: Array of prices
        period: Moving average period (default: 20)
        num_std: Number of standard deviations (default: 2.0)
        
    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    if len(prices) < period:
        return (
            np.full(len(prices), np.nan),
            np.full(len(prices), np.nan),
            np.full(len(prices), np.nan)
        )
    
    # Middle band is SMA
    middle_band = sma(prices, period)
    
    # Calculate rolling standard deviation
    std_dev = np.full(len(prices), np.nan)
    
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        std_dev[i] = np.std(window, ddof=1)
    
    # Upper and lower bands
    upper_band = middle_band + (num_std * std_dev)
    lower_band = middle_band - (num_std * std_dev)
    
    return upper_band, middle_band, lower_band


def standard_deviation(prices: np.ndarray, period: int = 20) -> np.ndarray:
    """
    Rolling Standard Deviation.
    
    Args:
        prices: Array of prices
        period: Rolling window period
        
    Returns:
        Array of standard deviation values
    """
    if len(prices) < period:
        return np.full(len(prices), np.nan)
    
    std_dev = np.full(len(prices), np.nan)
    
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        std_dev[i] = np.std(window, ddof=1)
    
    return std_dev


def historical_volatility(
    prices: np.ndarray,
    period: int = 20,
    annualization_factor: int = 252
) -> np.ndarray:
    """
    Historical Volatility (annualized).
    
    Uses log returns for calculation.
    
    Args:
        prices: Array of prices
        period: Lookback period
        annualization_factor: Trading days per year (default: 252)
        
    Returns:
        Array of annualized volatility values (as percentage)
    """
    if len(prices) < period + 1:
        return np.full(len(prices), np.nan)
    
    # Calculate log returns
    log_returns = np.log(prices[1:] / prices[:-1])
    
    # Calculate rolling std of log returns
    volatility = np.full(len(prices), np.nan)
    
    for i in range(period, len(log_returns) + 1):
        window = log_returns[i - period:i]
        volatility[i] = np.std(window, ddof=1) * np.sqrt(annualization_factor) * 100
    
    return volatility


def keltner_channels(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    ema_period: int = 20,
    atr_period: int = 10,
    atr_multiplier: float = 2.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Keltner Channels.
    Similar to Bollinger Bands but uses ATR instead of standard deviation.
    
    Middle Line = EMA of close
    Upper Channel = EMA + (ATR × multiplier)
    Lower Channel = EMA - (ATR × multiplier)
    
    Args:
        high: Array of high prices
        low: Array of low prices
        close: Array of close prices
        ema_period: EMA period (default: 20)
        atr_period: ATR period (default: 10)
        atr_multiplier: ATR multiplier (default: 2.0)
        
    Returns:
        Tuple of (upper_channel, middle_line, lower_channel)
    """
    # Middle line is EMA of close
    middle_line = ema(close, ema_period)
    
    # Calculate ATR
    atr_values = atr(high, low, close, atr_period)
    
    # Calculate channels
    upper_channel = middle_line + (atr_multiplier * atr_values)
    lower_channel = middle_line - (atr_multiplier * atr_values)
    
    return upper_channel, middle_line, lower_channel


def donchian_channels(
    high: np.ndarray,
    low: np.ndarray,
    period: int = 20
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Donchian Channels.
    
    Upper Channel = Highest high over period
    Lower Channel = Lowest low over period
    Middle Channel = (Upper + Lower) / 2
    
    Args:
        high: Array of high prices
        low: Array of low prices
        period: Lookback period (default: 20)
        
    Returns:
        Tuple of (upper_channel, middle_channel, lower_channel)
    """
    if len(high) < period:
        return (
            np.full(len(high), np.nan),
            np.full(len(high), np.nan),
            np.full(len(high), np.nan)
        )
    
    upper_channel = np.full(len(high), np.nan)
    lower_channel = np.full(len(low), np.nan)
    
    for i in range(period - 1, len(high)):
        upper_channel[i] = np.max(high[i - period + 1:i + 1])
        lower_channel[i] = np.min(low[i - period + 1:i + 1])
    
    middle_channel = (upper_channel + lower_channel) / 2
    
    return upper_channel, middle_channel, lower_channel


class Volatility:
    """
    Collection of volatility indicators.
    """
    
    @staticmethod
    def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """Average True Range."""
        return atr(high, low, close, period)
    
    @staticmethod
    def bollinger_bands(
        prices: np.ndarray,
        period: int = 20,
        num_std: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Bollinger Bands."""
        return bollinger_bands(prices, period, num_std)
    
    @staticmethod
    def std_dev(prices: np.ndarray, period: int = 20) -> np.ndarray:
        """Standard Deviation."""
        return standard_deviation(prices, period)
    
    @staticmethod
    def historical_vol(prices: np.ndarray, period: int = 20) -> np.ndarray:
        """Historical Volatility (annualized)."""
        return historical_volatility(prices, period)
    
    @staticmethod
    def keltner(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        ema_period: int = 20,
        atr_period: int = 10
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Keltner Channels."""
        return keltner_channels(high, low, close, ema_period, atr_period)
    
    @staticmethod
    def donchian(
        high: np.ndarray,
        low: np.ndarray,
        period: int = 20
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Donchian Channels."""
        return donchian_channels(high, low, period)
