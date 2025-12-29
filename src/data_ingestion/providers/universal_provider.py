"""
Universal File Data Provider
Loads ANY type of sequential data from local files for prediction tasks.

This provider is domain-agnostic and can handle:
- Market data (prices, volumes)
- Weather data (temperature, pressure, humidity)
- Sensor data (readings, measurements)
- Text metrics (sentiment scores, engagement)
- Health data (vitals, measurements)
- Any time-series or sequential data
"""

import os
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
import pandas as pd
from src.data_ingestion.base_provider import BaseProvider
from src.logger import get_logger


class UniversalFileProvider(BaseProvider):
    """
    Universal file-based data provider for loading ANY sequential data.
    
    The argmax equation ŷ = argmax_{x ∈ C} S(x | c) can predict anything.
    This provider ensures you can feed it any data type with proper formatting.
    
    Supports multiple file formats:
    - CSV: Standard comma-separated values
    - JSON: JSON array of records or line-delimited JSON
    - Parquet: Compressed columnar format (requires pyarrow)
    
    Directory Structure:
        data_directory/
            weather_NYC.csv       # Weather predictions
            sensor_01.json        # Sensor readings
            patient_123.parquet   # Health metrics
            text_sentiment.csv    # Text analysis
            subdomain/            # Optional subdirectory
                custom_data.csv
    
    Universal Data Format:
        Required columns:
            - timestamp: Time/sequence identifier (ISO 8601, Unix, or datetime)
            - value: Primary measurement/observation (or custom name)
        
        Optional columns:
            - Any additional features/measurements
            - Custom column names are preserved
    
    Examples of Use Cases:
        1. Weather Prediction:
           timestamp, temperature, humidity, pressure, wind_speed
        
        2. Sensor Monitoring:
           timestamp, sensor_reading, battery_level, signal_strength
        
        3. Text Analysis:
           timestamp, sentiment_score, engagement, word_count
        
        4. Health Monitoring:
           timestamp, heart_rate, blood_pressure, temperature
        
        5. Market Data (backward compatible):
           timestamp, open, high, low, close, volume
    """
    
    def __init__(
        self, 
        data_directory: Optional[str] = None,
        value_column: Optional[str] = None,
        schema_mode: str = 'flexible'
    ):
        """
        Initialize universal file data provider.
        
        Args:
            data_directory: Path to directory containing data files.
                          If None, uses 'data_directory' from provider config.
            value_column: Name of the primary value column.
                         If None, will auto-detect from common names.
            schema_mode: How to handle column validation:
                        'flexible' - Auto-detect and preserve all columns
                        'market' - Enforce market data schema (OHLCV)
                        'minimal' - Only require timestamp and one value column
        """
        super().__init__('file')
        
        # Get data directory from config or parameter
        if data_directory is None:
            data_directory = self.provider_config.get('data_directory', 'data/universal_data')
        
        self.data_directory = Path(data_directory)
        self.value_column = value_column
        self.schema_mode = schema_mode
        
        self.logger.info(
            f"Universal file provider initialized with directory: {self.data_directory}, "
            f"schema_mode: {schema_mode}"
        )
        
        # Validate directory exists
        if not self.data_directory.exists():
            self.logger.warning(
                f"Data directory does not exist: {self.data_directory}. "
                "Please create it and add data files."
            )
        
        # Supported file extensions
        self.supported_formats = {'.csv', '.json', '.parquet'}
        
        # Cache file paths for identifiers
        self._file_cache: Dict[str, Path] = {}
        self._scan_directory()
    
    def _scan_directory(self) -> None:
        """
        Scan data directory and cache file paths for each identifier.
        Supports subdirectories and case-insensitive matching.
        """
        if not self.data_directory.exists():
            return
        
        self._file_cache.clear()
        
        # Recursively find all data files
        for ext in self.supported_formats:
            for file_path in self.data_directory.rglob(f"*{ext}"):
                # Use filename (without extension) as identifier
                identifier = file_path.stem.upper()
                
                # Store first occurrence (prevents duplicates)
                if identifier not in self._file_cache:
                    self._file_cache[identifier] = file_path
                    self.logger.debug(f"Cached file for identifier {identifier}: {file_path}")
        
        self.logger.info(f"Scanned directory. Found {len(self._file_cache)} data files.")
    
    def _find_file(self, identifier: str) -> Optional[Path]:
        """
        Find data file for a given identifier.
        
        Args:
            identifier: Data identifier (case-insensitive)
            
        Returns:
            Path to data file or None if not found
        """
        identifier_upper = identifier.upper()
        
        # Check cache first
        if identifier_upper in self._file_cache:
            return self._file_cache[identifier_upper]
        
        # Rescan directory (in case new files were added)
        self._scan_directory()
        
        return self._file_cache.get(identifier_upper)
    
    def _load_csv(self, file_path: Path) -> pd.DataFrame:
        """Load data from CSV file."""
        try:
            df = pd.read_csv(file_path)
            
            # Check if any timestamp-like column exists and parse it
            timestamp_cols = ['timestamp', 'date', 'datetime', 'time', 'ts', 'sequence']
            for col in df.columns:
                if col.lower() in timestamp_cols:
                    df[col] = pd.to_datetime(df[col])
                    break
            
            return df
        except Exception as e:
            self.logger.error(f"Error loading CSV {file_path}: {e}")
            raise
    
    def _load_json(self, file_path: Path) -> pd.DataFrame:
        """Load data from JSON file."""
        try:
            # Try standard JSON first
            try:
                df = pd.read_json(file_path)
                return df
            except ValueError:
                # Try line-delimited JSON
                df = pd.read_json(file_path, lines=True)
                return df
        except Exception as e:
            self.logger.error(f"Error loading JSON {file_path}: {e}")
            raise
    
    def _load_parquet(self, file_path: Path) -> pd.DataFrame:
        """Load data from Parquet file."""
        try:
            df = pd.read_parquet(file_path)
            return df
        except Exception as e:
            self.logger.error(f"Error loading Parquet {file_path}: {e}")
            raise
    
    def _load_file(self, file_path: Path) -> pd.DataFrame:
        """Load data file based on extension."""
        ext = file_path.suffix.lower()
        
        if ext == '.csv':
            return self._load_csv(file_path)
        elif ext == '.json':
            return self._load_json(file_path)
        elif ext == '.parquet':
            return self._load_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def _normalize_dataframe(self, df: pd.DataFrame, identifier: str) -> pd.DataFrame:
        """
        Normalize DataFrame with flexible schema support.
        
        Args:
            df: Raw DataFrame from file
            identifier: Data identifier
            
        Returns:
            Normalized DataFrame with standardized timestamp column
        """
        # Create a copy to avoid modifying original
        df = df.copy()
        
        # Normalize column names (case-insensitive)
        df.columns = [col.lower() for col in df.columns]
        
        # Ensure timestamp column exists
        if 'timestamp' not in df.columns:
            # Try common alternatives
            timestamp_alternatives = ['date', 'datetime', 'time', 'ts', 'sequence', 'index']
            found = False
            for alt in timestamp_alternatives:
                if alt in df.columns:
                    df = df.rename(columns={alt: 'timestamp'})
                    found = True
                    break
            
            if not found:
                raise ValueError(
                    f"Missing timestamp column. Expected 'timestamp' or alternatives: "
                    f"{timestamp_alternatives}"
                )
        
        # Convert timestamp to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            try:
                # Try parsing as ISO string or standard datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            except (ValueError, TypeError):
                try:
                    # Try parsing as Unix timestamp
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Could not parse timestamp column: {e}")
                    raise
        
        # Handle schema modes
        if self.schema_mode == 'market':
            # Backward compatible market data mode
            df = self._apply_market_schema(df)
        elif self.schema_mode == 'minimal':
            # Ensure at least one value column exists
            df = self._apply_minimal_schema(df)
        # 'flexible' mode: preserve all columns as-is
        
        # Add identifier column
        df['identifier'] = identifier.upper()
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        return df
    
    def _apply_market_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply market data schema (OHLCV)."""
        # Try to find close/price column
        value_cols = ['close', 'price', 'last', 'value']
        close_col = None
        for col in value_cols:
            if col in df.columns:
                close_col = col
                if col != 'close':
                    df = df.rename(columns={col: 'close'})
                break
        
        if close_col is None:
            raise ValueError(
                f"Missing value column for market mode. "
                f"Expected one of: {value_cols}"
            )
        
        # Ensure OHLCV columns exist (fill with close if missing)
        ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in ohlcv_cols:
            if col not in df.columns:
                if col in ['open', 'high', 'low']:
                    df[col] = df['close']
                elif col == 'volume':
                    df[col] = 0.0
        
        return df
    
    def _apply_minimal_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure minimal schema (timestamp + at least one value column)."""
        # Check if we have at least one numeric column besides timestamp
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if len(numeric_cols) == 0:
            # Try to find a value column with common names
            value_alternatives = ['value', 'measurement', 'reading', 'score', 'metric', 
                                'close', 'price', 'amount', 'quantity']
            found = False
            for alt in value_alternatives:
                if alt in df.columns:
                    # Ensure it's numeric
                    try:
                        df[alt] = pd.to_numeric(df[alt])
                        found = True
                        break
                    except (ValueError, TypeError):
                        continue
            
            if not found:
                raise ValueError(
                    "No numeric value column found. Data must contain at least one "
                    "numeric measurement column."
                )
        
        return df
    
    def fetch_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch current (latest) data point for an identifier.
        
        Note: Method name kept for backward compatibility with BaseProvider.
        For universal data, this returns the latest data point.
        
        Args:
            symbol: Data identifier (matches filename without extension)
            
        Returns:
            Dictionary with timestamp, identifier, and all data columns
        """
        if not self.validate_symbol(symbol):
            self.logger.error(f"Invalid identifier: {symbol}")
            return None
        
        try:
            # Find file for identifier
            file_path = self._find_file(symbol)
            if file_path is None:
                self.logger.error(f"No data file found for identifier: {symbol}")
                return None
            
            self.logger.info(f"Loading latest data for {symbol} from {file_path}")
            
            # Load and normalize data
            df = self._load_file(file_path)
            df = self._normalize_dataframe(df, symbol)
            
            if df.empty:
                self.logger.warning(f"No data in file for {symbol}")
                return None
            
            # Get latest record
            latest = df.iloc[-1]
            
            # Convert to dictionary, preserving all columns
            result = {
                'timestamp': latest['timestamp'].to_pydatetime(),
                'identifier': symbol.upper()
            }
            
            # Add all other columns dynamically
            for col in df.columns:
                if col not in ['timestamp', 'identifier']:
                    result[col] = float(latest[col]) if pd.api.types.is_numeric_dtype(df[col]) else latest[col]
            
            self.logger.info(f"Fetched latest data for {symbol}")
            return result
            
        except Exception as e:
            self._handle_error(e, f"fetching latest data for {symbol}")
            return None
    
    def fetch_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = '1d'
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch historical data from file.
        
        Note: The 'interval' parameter is ignored for file provider
        as the data interval is determined by the file content.
        
        Args:
            symbol: Data identifier
            start_date: Start date for filtering
            end_date: End date for filtering
            interval: Ignored for file provider
            
        Returns:
            List of data dictionaries with all columns preserved
        """
        if not self.validate_symbol(symbol):
            self.logger.error(f"Invalid identifier: {symbol}")
            return None
        
        try:
            # Find file for identifier
            file_path = self._find_file(symbol)
            if file_path is None:
                self.logger.error(f"No data file found for identifier: {symbol}")
                return None
            
            self.logger.info(
                f"Loading historical data for {symbol} from {start_date} to {end_date}"
            )
            
            # Load and normalize data
            df = self._load_file(file_path)
            df = self._normalize_dataframe(df, symbol)
            
            if df.empty:
                self.logger.warning(f"No data in file for {symbol}")
                return None
            
            # Filter by date range
            mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
            df_filtered = df.loc[mask]
            
            if df_filtered.empty:
                self.logger.warning(
                    f"No data for {symbol} in date range {start_date} to {end_date}"
                )
                return None
            
            # Convert to list of dictionaries, preserving all columns
            result = []
            for _, row in df_filtered.iterrows():
                data_point = {
                    'timestamp': row['timestamp'].to_pydatetime(),
                    'identifier': symbol.upper()
                }
                
                # Add all other columns dynamically
                for col in df_filtered.columns:
                    if col not in ['timestamp', 'identifier']:
                        data_point[col] = float(row[col]) if pd.api.types.is_numeric_dtype(df_filtered[col]) else row[col]
                
                result.append(data_point)
            
            self.logger.info(
                f"Fetched {len(result)} historical records for {symbol}"
            )
            return result
            
        except Exception as e:
            self._handle_error(e, f"fetching historical data for {symbol}")
            return None
    
    def list_available_identifiers(self) -> List[str]:
        """
        List all available data identifiers in the data directory.
        
        Returns:
            List of identifier names
        """
        self._scan_directory()
        return sorted(list(self._file_cache.keys()))
    
    def list_available_symbols(self) -> List[str]:
        """Backward compatibility alias for list_available_identifiers."""
        return self.list_available_identifiers()
    
    def refresh_cache(self) -> None:
        """Refresh the file cache by rescanning the directory."""
        self.logger.info("Refreshing file cache...")
        self._scan_directory()
    
    def get_data_schema(self, identifier: str) -> Optional[Dict[str, str]]:
        """
        Get the schema (column names and types) for a data file.
        
        Args:
            identifier: Data identifier
            
        Returns:
            Dictionary mapping column names to data types
        """
        try:
            file_path = self._find_file(identifier)
            if file_path is None:
                return None
            
            df = self._load_file(file_path)
            
            # Get column types
            schema = {}
            for col in df.columns:
                dtype = df[col].dtype
                if pd.api.types.is_numeric_dtype(dtype):
                    schema[col] = 'numeric'
                elif pd.api.types.is_datetime64_any_dtype(dtype):
                    schema[col] = 'datetime'
                elif pd.api.types.is_string_dtype(dtype):
                    schema[col] = 'string'
                else:
                    schema[col] = str(dtype)
            
            return schema
            
        except Exception as e:
            self.logger.error(f"Error getting schema for {identifier}: {e}")
            return None
