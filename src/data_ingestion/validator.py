"""
Data Validator
Validates data quality and detects anomalies
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from src.logger import get_logger
from src.config_loader import get_config


class DataValidator:
    """
    Validate data quality and detect anomalies.
    Ensures data integrity before feeding into the system.
    """
    
    def __init__(self):
        """Initialize data validator."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # Load validation configuration
        val_config = self.config.get('validation', {})
        self.price_config = val_config.get('price', {})
        self.volume_config = val_config.get('volume', {})
        self.timestamp_config = val_config.get('timestamp', {})
        
        # Outlier detection configuration
        outlier_config = self.config.get('normalization.outlier_detection', {})
        self.outlier_enabled = outlier_config.get('enabled', True)
        self.outlier_method = outlier_config.get('method', 'iqr')
        self.outlier_threshold = outlier_config.get('threshold', 3.0)
    
    def validate_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a single data record.
        
        Args:
            record: Data record to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate timestamp
        if not self._validate_timestamp(record.get('timestamp')):
            errors.append("Invalid or missing timestamp")
        
        # Validate symbol
        if not record.get('symbol'):
            errors.append("Missing symbol")
        
        # Validate prices
        price_error = self._validate_prices(record)
        if price_error:
            errors.append(price_error)
        
        # Validate volume
        if not self._validate_volume(record.get('volume')):
            errors.append("Invalid volume")
        
        # Check for OHLC consistency
        ohlc_error = self._validate_ohlc_consistency(record)
        if ohlc_error:
            errors.append(ohlc_error)
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def validate_batch(
        self,
        records: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validate a batch of records.
        
        Args:
            records: List of data records
            
        Returns:
            Tuple of (valid_records, invalid_records_with_errors)
        """
        valid_records = []
        invalid_records = []
        
        for record in records:
            is_valid, errors = self.validate_record(record)
            
            if is_valid:
                valid_records.append(record)
            else:
                invalid_record = record.copy()
                invalid_record['validation_errors'] = errors
                invalid_records.append(invalid_record)
        
        if invalid_records:
            self.logger.warning(
                f"Validation failed for {len(invalid_records)}/{len(records)} records"
            )
        
        return valid_records, invalid_records
    
    def detect_outliers(
        self,
        records: List[Dict[str, Any]],
        field: str = 'close'
    ) -> List[int]:
        """
        Detect outliers in a series using configured method.
        
        Args:
            records: List of data records
            field: Field to check for outliers (default: 'close')
            
        Returns:
            List of indices where outliers were detected
        """
        if not self.outlier_enabled or not records:
            return []
        
        values = np.array([r.get(field) for r in records if r.get(field) is not None])
        
        if len(values) < 4:
            return []
        
        if self.outlier_method == 'iqr':
            return self._detect_outliers_iqr(values)
        elif self.outlier_method == 'zscore':
            return self._detect_outliers_zscore(values)
        else:
            self.logger.warning(f"Unknown outlier method: {self.outlier_method}")
            return []
    
    def _validate_timestamp(self, timestamp: Any) -> bool:
        """Validate timestamp."""
        if not isinstance(timestamp, datetime):
            return False
        
        # Check if timestamp is within reasonable range
        min_year = self.timestamp_config.get('min_year', 2000)
        max_future_days = self.timestamp_config.get('max_future_days', 1)
        
        min_date = datetime(min_year, 1, 1)
        max_date = datetime.now() + timedelta(days=max_future_days)
        
        return min_date <= timestamp <= max_date
    
    def _validate_prices(self, record: Dict[str, Any]) -> Optional[str]:
        """Validate price values."""
        price_fields = ['open', 'high', 'low', 'close']
        prices = {field: record.get(field) for field in price_fields}
        
        # At minimum, close price must exist
        if prices['close'] is None:
            return "Missing close price"
        
        # Validate price ranges
        min_price = self.price_config.get('min', 0)
        max_price = self.price_config.get('max', 1000000000)
        
        for field, price in prices.items():
            if price is not None:
                if not (min_price <= price <= max_price):
                    return f"Price {field}={price} out of range [{min_price}, {max_price}]"
        
        return None
    
    def _validate_volume(self, volume: Any) -> bool:
        """Validate volume."""
        if volume is None:
            return True  # Volume is optional
        
        min_volume = self.volume_config.get('min', 0)
        return volume >= min_volume
    
    def _validate_ohlc_consistency(self, record: Dict[str, Any]) -> Optional[str]:
        """
        Validate OHLC consistency: high >= low, high >= open/close, low <= open/close.
        
        Args:
            record: Data record
            
        Returns:
            Error message if inconsistent, None otherwise
        """
        open_price = record.get('open')
        high = record.get('high')
        low = record.get('low')
        close = record.get('close')
        
        # If any OHLC is missing, skip consistency check
        if None in [open_price, high, low, close]:
            return None
        
        # High must be >= low
        if high < low:
            return f"High ({high}) < Low ({low})"
        
        # High must be >= open and close
        if high < open_price or high < close:
            return f"High ({high}) less than open or close"
        
        # Low must be <= open and close
        if low > open_price or low > close:
            return f"Low ({low}) greater than open or close"
        
        return None
    
    def _detect_outliers_iqr(self, values: np.ndarray) -> List[int]:
        """
        Detect outliers using Interquartile Range (IQR) method.
        
        Args:
            values: Array of values
            
        Returns:
            List of outlier indices
        """
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - self.outlier_threshold * iqr
        upper_bound = q3 + self.outlier_threshold * iqr
        
        outliers = np.where((values < lower_bound) | (values > upper_bound))[0]
        return outliers.tolist()
    
    def _detect_outliers_zscore(self, values: np.ndarray) -> List[int]:
        """
        Detect outliers using Z-score method.
        
        Args:
            values: Array of values
            
        Returns:
            List of outlier indices
        """
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:
            return []
        
        z_scores = np.abs((values - mean) / std)
        outliers = np.where(z_scores > self.outlier_threshold)[0]
        
        return outliers.tolist()
