"""
File Data Provider
Loads market data from local files (CSV, JSON, Parquet) in a designated directory.

This provider enables offline data analysis and backtesting without API dependencies.
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import pandas as pd
from src.data_ingestion.base_provider import BaseProvider
from src.logger import get_logger


class FileDataProvider(BaseProvider):
    """
    File-based data provider for loading OHLCV data from local files.
    
    Supports multiple file formats:
    - CSV: Standard comma-separated values
    - JSON: JSON array of records or line-delimited JSON
    - Parquet: Compressed columnar format (requires pyarrow)
    
    Directory Structure:
        data_directory/
            AAPL.csv          # Symbol-based files
            BTCUSD.json       # Any supported format
            gold.parquet      # Case-insensitive matching
            historical/       # Optional subdirectory
                MSFT.csv
    
    Expected Data Format (columns can be in any order):
        - timestamp: ISO 8601 string, Unix timestamp, or datetime
        - open: Opening price
        - high: High price
        - low: Low price
        - close: Close price
        - volume: Trading volume (optional)
    """
    
    def __init__(self, data_directory: Optional[str] = None):
        """
        Initialize file data provider.
        
        Args:
            data_directory: Path to directory containing data files.
                          If None, uses 'data_directory' from provider config.
        """
        super().__init__('file')
        
        # Get data directory from config or parameter
        if data_directory is None:
            data_directory = self.provider_config.get('data_directory', 'data/market_data')
        
        self.data_directory = Path(data_directory)
        self.logger.info(f"File provider initialized with directory: {self.data_directory}")
        
        # Validate directory exists
        if not self.data_directory.exists():
            self.logger.warning(
                f"Data directory does not exist: {self.data_directory}. "
                "Please create it and add data files."
            )
        
        # Supported file extensions
        self.supported_formats = {'.csv', '.json', '.parquet'}
        
        # Cache file paths for symbols
        self._file_cache: Dict[str, Path] = {}
        self._scan_directory()
    
    def _scan_directory(self) -> None:
        """
        Scan data directory and cache file paths for each symbol.
        Supports subdirectories and case-insensitive matching.
        """
        if not self.data_directory.exists():
            return
        
        self._file_cache.clear()
        
        # Recursively find all data files
        for ext in self.supported_formats:
            for file_path in self.data_directory.rglob(f"*{ext}"):
                # Use filename (without extension) as symbol
                symbol = file_path.stem.upper()
                
                # Store first occurrence (prevents duplicates)
                if symbol not in self._file_cache:
                    self._file_cache[symbol] = file_path
                    self.logger.debug(f"Cached file for symbol {symbol}: {file_path}")
        
        self.logger.info(f"Scanned directory. Found {len(self._file_cache)} symbol files.")
    
    def _find_file(self, symbol: str) -> Optional[Path]:
        """
        Find data file for a given symbol.
        
        Args:
            symbol: Symbol to search for (case-insensitive)
            
        Returns:
            Path to data file or None if not found
        """
        symbol_upper = symbol.upper()
        
        # Check cache first
        if symbol_upper in self._file_cache:
            return self._file_cache[symbol_upper]
        
        # Rescan directory (in case new files were added)
        self._scan_directory()
        
        return self._file_cache.get(symbol_upper)
    
    def _load_csv(self, file_path: Path) -> pd.DataFrame:
        """
        Load data from CSV file.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            DataFrame with loaded data
        """
        try:
            # Try to automatically parse dates with common timestamp column names
            df = pd.read_csv(file_path)
            
            # Check if any timestamp-like column exists and parse it
            timestamp_cols = ['timestamp', 'date', 'datetime', 'time', 'ts']
            for col in df.columns:
                if col.lower() in timestamp_cols:
                    df[col] = pd.to_datetime(df[col])
                    break
            
            return df
        except Exception as e:
            self.logger.error(f"Error loading CSV {file_path}: {e}")
            raise
    
    def _load_json(self, file_path: Path) -> pd.DataFrame:
        """
        Load data from JSON file.
        Supports both JSON array and line-delimited JSON (JSONL).
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            DataFrame with loaded data
        """
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
        """
        Load data from Parquet file.
        
        Args:
            file_path: Path to Parquet file
            
        Returns:
            DataFrame with loaded data
        """
        try:
            df = pd.read_parquet(file_path)
            return df
        except Exception as e:
            self.logger.error(f"Error loading Parquet {file_path}: {e}")
            raise
    
    def _load_file(self, file_path: Path) -> pd.DataFrame:
        """
        Load data file based on extension.
        
        Args:
            file_path: Path to data file
            
        Returns:
            DataFrame with loaded data
        """
        ext = file_path.suffix.lower()
        
        if ext == '.csv':
            return self._load_csv(file_path)
        elif ext == '.json':
            return self._load_json(file_path)
        elif ext == '.parquet':
            return self._load_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def _normalize_dataframe(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Normalize DataFrame to expected format.
        
        Args:
            df: Raw DataFrame from file
            symbol: Symbol name
            
        Returns:
            Normalized DataFrame with standardized columns
        """
        # Create a copy to avoid modifying original
        df = df.copy()
        
        # Normalize column names (case-insensitive)
        df.columns = [col.lower() for col in df.columns]
        
        # Ensure required columns exist
        required_cols = ['timestamp', 'close']
        for col in required_cols:
            if col not in df.columns:
                # Try common alternatives
                alternatives = {
                    'timestamp': ['date', 'datetime', 'time', 'ts'],
                    'close': ['price', 'last']
                }
                
                found = False
                for alt in alternatives.get(col, []):
                    if alt in df.columns:
                        df = df.rename(columns={alt: col})
                        found = True
                        break
                
                if not found:
                    raise ValueError(f"Missing required column: {col}")
        
        # Convert timestamp to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            try:
                # Try parsing as ISO string
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            except (ValueError, TypeError):
                try:
                    # Try parsing as Unix timestamp
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Could not parse timestamp column: {e}")
                    raise
        
        # Ensure OHLCV columns exist (fill with close if missing)
        ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in ohlcv_cols:
            if col not in df.columns:
                if col in ['open', 'high', 'low']:
                    # Use close price as fallback for OHLC
                    df[col] = df['close']
                elif col == 'volume':
                    # Volume is optional
                    df[col] = 0.0
        
        # Add symbol column
        df['symbol'] = symbol.upper()
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        return df
    
    def fetch_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch current (latest) price for a symbol from file.
        
        Args:
            symbol: Ticker symbol (matches filename without extension)
            
        Returns:
            Dictionary with timestamp, symbol, OHLCV data
        """
        if not self.validate_symbol(symbol):
            self.logger.error(f"Invalid symbol: {symbol}")
            return None
        
        try:
            # Find file for symbol
            file_path = self._find_file(symbol)
            if file_path is None:
                self.logger.error(f"No data file found for symbol: {symbol}")
                return None
            
            self.logger.info(f"Loading current price for {symbol} from {file_path}")
            
            # Load and normalize data
            df = self._load_file(file_path)
            df = self._normalize_dataframe(df, symbol)
            
            if df.empty:
                self.logger.warning(f"No data in file for {symbol}")
                return None
            
            # Get latest record
            latest = df.iloc[-1]
            
            result = {
                'timestamp': latest['timestamp'].to_pydatetime(),
                'symbol': symbol.upper(),
                'open': float(latest['open']),
                'high': float(latest['high']),
                'low': float(latest['low']),
                'close': float(latest['close']),
                'volume': float(latest['volume'])
            }
            
            self.logger.info(f"Fetched current price for {symbol}: ${result['close']}")
            return result
            
        except Exception as e:
            self._handle_error(e, f"fetching current price for {symbol}")
            return None
    
    def fetch_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = '1d'
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch historical price data from file.
        
        Note: The 'interval' parameter is ignored for file provider
        as the data interval is determined by the file content.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date for filtering
            end_date: End date for filtering
            interval: Ignored for file provider
            
        Returns:
            List of OHLCV data dictionaries
        """
        if not self.validate_symbol(symbol):
            self.logger.error(f"Invalid symbol: {symbol}")
            return None
        
        try:
            # Find file for symbol
            file_path = self._find_file(symbol)
            if file_path is None:
                self.logger.error(f"No data file found for symbol: {symbol}")
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
            
            # Convert to list of dictionaries
            result = []
            for _, row in df_filtered.iterrows():
                data_point = {
                    'timestamp': row['timestamp'].to_pydatetime(),
                    'symbol': symbol.upper(),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume'])
                }
                result.append(data_point)
            
            self.logger.info(
                f"Fetched {len(result)} historical records for {symbol}"
            )
            return result
            
        except Exception as e:
            self._handle_error(e, f"fetching historical data for {symbol}")
            return None
    
    def list_available_symbols(self) -> List[str]:
        """
        List all available symbols in the data directory.
        
        Returns:
            List of symbol names
        """
        self._scan_directory()
        return sorted(list(self._file_cache.keys()))
    
    def refresh_cache(self) -> None:
        """Refresh the file cache by rescanning the directory."""
        self.logger.info("Refreshing file cache...")
        self._scan_directory()
