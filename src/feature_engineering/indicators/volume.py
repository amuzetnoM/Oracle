"""
Volume Indicators
OBV, Volume Profile, VWAP - Pure numpy implementations
"""

import numpy as np
from typing import Tuple
from src.logger import get_logger


logger = get_logger(__name__)


def obv(close: np.ndarray, volume: np.ndarray) -> np.ndarray:
    """
    On-Balance Volume (OBV).
    Cumulative volume indicator based on price direction.
    
    OBV increases by volume when price rises
    OBV decreases by volume when price falls
    
    Args:
        close: Array of close prices
        volume: Array of volumes
        
    Returns:
        Array of OBV values
    """
    if len(close) != len(volume) or len(close) < 2:
        return np.full(len(close), np.nan)
    
    obv_values = np.zeros(len(close))
    obv_values[0] = volume[0]
    
    for i in range(1, len(close)):
        if close[i] > close[i-1]:
            obv_values[i] = obv_values[i-1] + volume[i]
        elif close[i] < close[i-1]:
            obv_values[i] = obv_values[i-1] - volume[i]
        else:
            obv_values[i] = obv_values[i-1]
    
    return obv_values


def vwap(high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray) -> np.ndarray:
    """
    Volume Weighted Average Price (VWAP).
    Intraday indicator showing average price weighted by volume.
    
    Args:
        high: Array of high prices
        low: Array of low prices
        close: Array of close prices
        volume: Array of volumes
        
    Returns:
        Array of VWAP values
    """
    if len(close) != len(volume):
        return np.full(len(close), np.nan)
    
    # Typical price
    typical_price = (high + low + close) / 3
    
    # Cumulative (typical price * volume)
    cumulative_tp_volume = np.cumsum(typical_price * volume)
    cumulative_volume = np.cumsum(volume)
    
    # VWAP
    vwap_values = cumulative_tp_volume / (cumulative_volume + 1e-10)
    
    return vwap_values


def volume_rate_of_change(volume: np.ndarray, period: int = 10) -> np.ndarray:
    """
    Volume Rate of Change.
    
    VROC = ((Current Volume - Volume N periods ago) / Volume N periods ago) * 100
    
    Args:
        volume: Array of volumes
        period: Lookback period
        
    Returns:
        Array of Volume ROC values (percentage)
    """
    if len(volume) < period + 1:
        return np.full(len(volume), np.nan)
    
    result = np.full(len(volume), np.nan)
    result[period:] = ((volume[period:] - volume[:-period]) / (volume[:-period] + 1e-10)) * 100
    
    return result


def accumulation_distribution(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    volume: np.ndarray
) -> np.ndarray:
    """
    Accumulation/Distribution Line.
    
    Money Flow Multiplier = ((Close - Low) - (High - Close)) / (High - Low)
    Money Flow Volume = Money Flow Multiplier × Volume
    A/D = Cumulative Money Flow Volume
    
    Args:
        high: Array of high prices
        low: Array of low prices
        close: Array of close prices
        volume: Array of volumes
        
    Returns:
        Array of A/D line values
    """
    if len(close) != len(volume):
        return np.full(len(close), np.nan)
    
    # Money Flow Multiplier
    mfm = np.zeros(len(close))
    
    for i in range(len(close)):
        if high[i] != low[i]:
            mfm[i] = ((close[i] - low[i]) - (high[i] - close[i])) / (high[i] - low[i])
        else:
            mfm[i] = 0
    
    # Money Flow Volume
    mfv = mfm * volume
    
    # Accumulation/Distribution Line
    ad_line = np.cumsum(mfv)
    
    return ad_line


def chaikin_money_flow(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    volume: np.ndarray,
    period: int = 20
) -> np.ndarray:
    """
    Chaikin Money Flow (CMF).
    
    Args:
        high: Array of high prices
        low: Array of low prices
        close: Array of close prices
        volume: Array of volumes
        period: CMF period (default: 20)
        
    Returns:
        Array of CMF values
    """
    if len(close) < period:
        return np.full(len(close), np.nan)
    
    # Money Flow Multiplier
    mfm = np.zeros(len(close))
    
    for i in range(len(close)):
        if high[i] != low[i]:
            mfm[i] = ((close[i] - low[i]) - (high[i] - close[i])) / (high[i] - low[i])
        else:
            mfm[i] = 0
    
    # Money Flow Volume
    mfv = mfm * volume
    
    # Calculate CMF
    cmf = np.full(len(close), np.nan)
    
    for i in range(period - 1, len(close)):
        sum_mfv = np.sum(mfv[i - period + 1:i + 1])
        sum_volume = np.sum(volume[i - period + 1:i + 1])
        
        if sum_volume > 0:
            cmf[i] = sum_mfv / sum_volume
    
    return cmf


def force_index(close: np.ndarray, volume: np.ndarray, period: int = 13) -> np.ndarray:
    """
    Force Index.
    
    Force Index = (Close - Previous Close) × Volume
    Then smooth with EMA
    
    Args:
        close: Array of close prices
        volume: Array of volumes
        period: EMA smoothing period (default: 13)
        
    Returns:
        Array of Force Index values
    """
    if len(close) != len(volume) or len(close) < period + 1:
        return np.full(len(close), np.nan)
    
    # Raw force index
    raw_fi = np.zeros(len(close))
    raw_fi[1:] = (close[1:] - close[:-1]) * volume[1:]
    
    # Smooth with EMA
    from src.feature_engineering.indicators.moving_averages import ema
    force_idx = ema(raw_fi, period)
    
    return force_idx


def ease_of_movement(
    high: np.ndarray,
    low: np.ndarray,
    volume: np.ndarray,
    period: int = 14
) -> np.ndarray:
    """
    Ease of Movement (EMV).
    
    Distance Moved = ((High + Low) / 2) - ((Prior High + Prior Low) / 2)
    Box Ratio = (Volume / scale) / (High - Low)
    EMV = Distance Moved / Box Ratio
    
    Args:
        high: Array of high prices
        low: Array of low prices
        volume: Array of volumes
        period: Smoothing period (default: 14)
        
    Returns:
        Array of EMV values
    """
    if len(high) < period + 1:
        return np.full(len(high), np.nan)
    
    # Distance moved
    midpoint = (high + low) / 2
    distance = np.zeros(len(high))
    distance[1:] = midpoint[1:] - midpoint[:-1]
    
    # Box ratio
    box_ratio = volume / (high - low + 1e-10)
    
    # EMV
    emv = distance / (box_ratio + 1e-10)
    
    # Smooth with SMA
    from src.feature_engineering.indicators.moving_averages import sma
    emv_smooth = sma(emv, period)
    
    return emv_smooth


class Volume:
    """
    Collection of volume indicators.
    """
    
    @staticmethod
    def obv(close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """On-Balance Volume."""
        return obv(close, volume)
    
    @staticmethod
    def vwap(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        volume: np.ndarray
    ) -> np.ndarray:
        """Volume Weighted Average Price."""
        return vwap(high, low, close, volume)
    
    @staticmethod
    def vroc(volume: np.ndarray, period: int = 10) -> np.ndarray:
        """Volume Rate of Change."""
        return volume_rate_of_change(volume, period)
    
    @staticmethod
    def ad_line(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        volume: np.ndarray
    ) -> np.ndarray:
        """Accumulation/Distribution Line."""
        return accumulation_distribution(high, low, close, volume)
    
    @staticmethod
    def cmf(
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        volume: np.ndarray,
        period: int = 20
    ) -> np.ndarray:
        """Chaikin Money Flow."""
        return chaikin_money_flow(high, low, close, volume, period)
    
    @staticmethod
    def force_idx(close: np.ndarray, volume: np.ndarray, period: int = 13) -> np.ndarray:
        """Force Index."""
        return force_index(close, volume, period)
    
    @staticmethod
    def emv(
        high: np.ndarray,
        low: np.ndarray,
        volume: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """Ease of Movement."""
        return ease_of_movement(high, low, volume, period)
