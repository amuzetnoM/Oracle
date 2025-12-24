"""
Data Normalizer
Standardizes data formats from different providers into a unified structure
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from src.logger import get_logger
from src.config_loader import get_config


class DataNormalizer:
    """
    Normalize data from various providers into a unified format.
    
    Unified format:
    {
        'timestamp': datetime (UTC),
        'symbol': str,
        'open': float,
        'high': float,
        'low': float,
        'close': float,
        'volume': float,
        'provider': str
    }
    """
    
    def __init__(self):
        """Initialize data normalizer."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # Get normalization configuration
        norm_config = self.config.get('normalization', {})
        self.timestamp_format = norm_config.get('timestamp_format', 'iso8601')
        self.timezone = norm_config.get('timezone', 'UTC')
        self.missing_strategy = norm_config.get('missing_value_strategy', 'forward_fill')
    
    def normalize_ohlcv(
        self,
        data: Dict[str, Any],
        provider: str
    ) -> Optional[Dict[str, Any]]:
        """
        Normalize OHLCV data from a provider.
        
        Args:
            data: Raw data from provider
            provider: Provider name
            
        Returns:
            Normalized data dictionary or None if normalization fails
        """
        try:
            normalized = {
                'timestamp': self._normalize_timestamp(data.get('timestamp')),
                'symbol': str(data.get('symbol', '')).upper(),
                'open': self._to_float(data.get('open')),
                'high': self._to_float(data.get('high')),
                'low': self._to_float(data.get('low')),
                'close': self._to_float(data.get('close')),
                'volume': self._to_float(data.get('volume', 0)),
                'provider': provider
            }
            
            # Validate essential fields
            if not all([
                normalized['timestamp'],
                normalized['symbol'],
                normalized['close'] is not None
            ]):
                self.logger.warning(f"Missing essential fields in data: {data}")
                return None
            
            return normalized
            
        except Exception as e:
            self.logger.error(f"Normalization error: {e}")
            return None
    
    def normalize_batch(
        self,
        data_list: List[Dict[str, Any]],
        provider: str
    ) -> List[Dict[str, Any]]:
        """
        Normalize a batch of data records.
        
        Args:
            data_list: List of raw data records
            provider: Provider name
            
        Returns:
            List of normalized records (excludes failed normalizations)
        """
        normalized_list = []
        
        for data in data_list:
            normalized = self.normalize_ohlcv(data, provider)
            if normalized:
                normalized_list.append(normalized)
        
        # Handle missing values if requested
        if self.missing_strategy == 'forward_fill' and normalized_list:
            normalized_list = self._forward_fill(normalized_list)
        
        return normalized_list
    
    def _normalize_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """
        Normalize timestamp to datetime object in UTC.
        
        Args:
            timestamp: Timestamp in various formats
            
        Returns:
            datetime object in UTC or None if conversion fails
        """
        try:
            if isinstance(timestamp, datetime):
                # Ensure UTC timezone
                if timestamp.tzinfo is None:
                    return timestamp.replace(tzinfo=timezone.utc)
                return timestamp.astimezone(timezone.utc)
            
            elif isinstance(timestamp, (int, float)):
                # Assume Unix timestamp
                return datetime.fromtimestamp(timestamp, tz=timezone.utc)
            
            elif isinstance(timestamp, str):
                # Try to parse ISO format
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            
            else:
                return None
                
        except Exception as e:
            self.logger.warning(f"Timestamp conversion failed: {e}")
            return None
    
    def _to_float(self, value: Any) -> Optional[float]:
        """
        Convert value to float safely.
        
        Args:
            value: Value to convert
            
        Returns:
            Float value or None if conversion fails
        """
        try:
            if value is None or value == '':
                return None
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _forward_fill(
        self,
        data_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Forward fill missing values in a time series.
        
        Args:
            data_list: List of normalized data records (sorted by time)
            
        Returns:
            Data list with missing values filled
        """
        if not data_list:
            return data_list
        
        # Fields to forward fill
        fill_fields = ['open', 'high', 'low', 'close']
        
        for i in range(1, len(data_list)):
            for field in fill_fields:
                if data_list[i][field] is None and data_list[i-1][field] is not None:
                    data_list[i][field] = data_list[i-1][field]
        
        return data_list
    
    def to_dict_series(
        self,
        data_list: List[Dict[str, Any]]
    ) -> Dict[str, List[Any]]:
        """
        Convert list of dictionaries to dictionary of lists (columnar format).
        
        Args:
            data_list: List of normalized data records
            
        Returns:
            Dictionary with column names as keys and lists as values
        """
        if not data_list:
            return {}
        
        # Initialize columns
        columns = {key: [] for key in data_list[0].keys()}
        
        # Fill columns
        for record in data_list:
            for key, value in record.items():
                columns[key].append(value)
        
        return columns
