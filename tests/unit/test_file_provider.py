"""
Test File Data Provider
"""

import pytest
import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil
from src.data_ingestion.providers.file_provider import FileDataProvider


class TestFileDataProvider:
    """Test file-based data provider functionality."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_csv_data(self, temp_data_dir):
        """Create a sample CSV file."""
        csv_path = Path(temp_data_dir) / "AAPL.csv"
        data = {
            'timestamp': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'open': [150.0, 151.0, 152.0],
            'high': [152.0, 153.0, 154.0],
            'low': [149.0, 150.0, 151.0],
            'close': [151.0, 152.0, 153.0],
            'volume': [1000000, 1200000, 1100000]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return csv_path
    
    @pytest.fixture
    def sample_json_data(self, temp_data_dir):
        """Create a sample JSON file."""
        json_path = Path(temp_data_dir) / "BTCUSD.json"
        data = [
            {
                'timestamp': '2024-01-01T00:00:00Z',
                'open': 45000.0,
                'high': 46000.0,
                'low': 44500.0,
                'close': 45500.0,
                'volume': 1000.5
            },
            {
                'timestamp': '2024-01-02T00:00:00Z',
                'open': 45500.0,
                'high': 47000.0,
                'low': 45000.0,
                'close': 46500.0,
                'volume': 1200.75
            }
        ]
        with open(json_path, 'w') as f:
            json.dump(data, f)
        return json_path
    
    @pytest.fixture
    def sample_minimal_csv(self, temp_data_dir):
        """Create a minimal CSV file (only timestamp and close)."""
        csv_path = Path(temp_data_dir) / "MINIMAL.csv"
        data = {
            'timestamp': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'close': [100.0, 101.0, 102.0]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return csv_path
    
    def test_provider_initialization(self, temp_data_dir):
        """Test provider initializes correctly."""
        provider = FileDataProvider(temp_data_dir)
        assert provider is not None
        assert provider.provider_name == 'file'
        assert provider.data_directory == Path(temp_data_dir)
    
    def test_scan_directory(self, temp_data_dir, sample_csv_data, sample_json_data):
        """Test directory scanning finds files."""
        provider = FileDataProvider(temp_data_dir)
        
        # Should find both files
        assert 'AAPL' in provider._file_cache
        assert 'BTCUSD' in provider._file_cache
        assert len(provider._file_cache) == 2
    
    def test_list_available_symbols(self, temp_data_dir, sample_csv_data, sample_json_data):
        """Test listing available symbols."""
        provider = FileDataProvider(temp_data_dir)
        symbols = provider.list_available_symbols()
        
        assert 'AAPL' in symbols
        assert 'BTCUSD' in symbols
        assert len(symbols) == 2
    
    def test_fetch_current_price_csv(self, temp_data_dir, sample_csv_data):
        """Test fetching current price from CSV."""
        provider = FileDataProvider(temp_data_dir)
        result = provider.fetch_current_price('AAPL')
        
        assert result is not None
        assert result['symbol'] == 'AAPL'
        assert result['close'] == 153.0  # Last value
        assert result['volume'] == 1100000
        assert 'timestamp' in result
        assert isinstance(result['timestamp'], datetime)
    
    def test_fetch_current_price_json(self, temp_data_dir, sample_json_data):
        """Test fetching current price from JSON."""
        provider = FileDataProvider(temp_data_dir)
        result = provider.fetch_current_price('BTCUSD')
        
        assert result is not None
        assert result['symbol'] == 'BTCUSD'
        assert result['close'] == 46500.0  # Last value
        assert result['volume'] == 1200.75
        assert 'timestamp' in result
    
    def test_fetch_current_price_minimal(self, temp_data_dir, sample_minimal_csv):
        """Test fetching from minimal CSV (only timestamp and close)."""
        provider = FileDataProvider(temp_data_dir)
        result = provider.fetch_current_price('MINIMAL')
        
        assert result is not None
        assert result['symbol'] == 'MINIMAL'
        assert result['close'] == 102.0
        # Should auto-fill OHLC from close
        assert result['open'] == 102.0
        assert result['high'] == 102.0
        assert result['low'] == 102.0
        assert result['volume'] == 0.0
    
    def test_fetch_historical_data_csv(self, temp_data_dir, sample_csv_data):
        """Test fetching historical data from CSV."""
        provider = FileDataProvider(temp_data_dir)
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 3)
        
        result = provider.fetch_historical_data('AAPL', start_date, end_date)
        
        assert result is not None
        assert len(result) == 3
        assert result[0]['close'] == 151.0
        assert result[1]['close'] == 152.0
        assert result[2]['close'] == 153.0
    
    def test_fetch_historical_data_date_filter(self, temp_data_dir, sample_csv_data):
        """Test date filtering in historical data."""
        provider = FileDataProvider(temp_data_dir)
        
        # Fetch only middle record
        start_date = datetime(2024, 1, 2)
        end_date = datetime(2024, 1, 2)
        
        result = provider.fetch_historical_data('AAPL', start_date, end_date)
        
        assert result is not None
        assert len(result) == 1
        assert result[0]['close'] == 152.0
    
    def test_invalid_symbol(self, temp_data_dir):
        """Test handling of invalid symbol."""
        provider = FileDataProvider(temp_data_dir)
        result = provider.fetch_current_price('NONEXISTENT')
        
        assert result is None
    
    def test_case_insensitive_symbol_matching(self, temp_data_dir, sample_csv_data):
        """Test case-insensitive symbol matching."""
        provider = FileDataProvider(temp_data_dir)
        
        # Should match regardless of case
        result1 = provider.fetch_current_price('AAPL')
        result2 = provider.fetch_current_price('aapl')
        result3 = provider.fetch_current_price('Aapl')
        
        assert result1 is not None
        assert result2 is not None
        assert result3 is not None
        assert result1['close'] == result2['close'] == result3['close']
    
    def test_refresh_cache(self, temp_data_dir, sample_csv_data):
        """Test cache refresh functionality."""
        provider = FileDataProvider(temp_data_dir)
        
        # Initial cache
        initial_symbols = provider.list_available_symbols()
        assert len(initial_symbols) == 1
        
        # Add new file
        new_csv = Path(temp_data_dir) / "MSFT.csv"
        data = {
            'timestamp': ['2024-01-01'],
            'close': [380.0]
        }
        df = pd.DataFrame(data)
        df.to_csv(new_csv, index=False)
        
        # Refresh cache
        provider.refresh_cache()
        
        # Should find new file
        updated_symbols = provider.list_available_symbols()
        assert len(updated_symbols) == 2
        assert 'MSFT' in updated_symbols
    
    def test_subdirectory_support(self, temp_data_dir):
        """Test support for subdirectories."""
        # Create subdirectory with data
        subdir = Path(temp_data_dir) / "stocks"
        subdir.mkdir()
        
        csv_path = subdir / "GOOGL.csv"
        data = {
            'timestamp': ['2024-01-01'],
            'close': [140.0]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        
        provider = FileDataProvider(temp_data_dir)
        result = provider.fetch_current_price('GOOGL')
        
        assert result is not None
        assert result['symbol'] == 'GOOGL'
        assert result['close'] == 140.0
    
    def test_column_name_alternatives(self, temp_data_dir):
        """Test alternative column names are recognized."""
        # Create file with alternative column names
        csv_path = Path(temp_data_dir) / "TEST.csv"
        data = {
            'date': ['2024-01-01', '2024-01-02'],  # Alternative for 'timestamp'
            'price': [100.0, 101.0]  # Alternative for 'close'
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        
        provider = FileDataProvider(temp_data_dir)
        result = provider.fetch_current_price('TEST')
        
        assert result is not None
        assert result['close'] == 101.0
    
    def test_empty_file(self, temp_data_dir):
        """Test handling of empty file."""
        csv_path = Path(temp_data_dir) / "EMPTY.csv"
        df = pd.DataFrame(columns=['timestamp', 'close'])
        df.to_csv(csv_path, index=False)
        
        provider = FileDataProvider(temp_data_dir)
        result = provider.fetch_current_price('EMPTY')
        
        assert result is None
    
    def test_validate_symbol(self, temp_data_dir):
        """Test symbol validation."""
        provider = FileDataProvider(temp_data_dir)
        
        assert provider.validate_symbol('AAPL') == True
        assert provider.validate_symbol('BTC-USD') == True
        assert provider.validate_symbol('') == False
        assert provider.validate_symbol(None) == False
    
    def test_data_normalization(self, temp_data_dir):
        """Test data is properly normalized."""
        # Create file with mixed case columns
        csv_path = Path(temp_data_dir) / "MIXED.csv"
        data = {
            'TIMESTAMP': ['2024-01-01'],
            'Close': [100.0],
            'Volume': [1000000]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        
        provider = FileDataProvider(temp_data_dir)
        result = provider.fetch_current_price('MIXED')
        
        # Should normalize column names
        assert result is not None
        assert result['close'] == 100.0
        assert result['volume'] == 1000000


@pytest.mark.integration
class TestFileProviderIntegration:
    """Integration tests with real-world scenarios."""
    
    def test_integration_with_validation(self, temp_data_dir):
        """Test file provider with data validation."""
        from src.data_ingestion import DataValidator
        
        # Create valid data
        csv_path = Path(temp_data_dir) / "VALID.csv"
        data = {
            'timestamp': ['2024-01-01', '2024-01-02'],
            'open': [100.0, 101.0],
            'high': [102.0, 103.0],
            'low': [99.0, 100.0],
            'close': [101.0, 102.0],
            'volume': [1000000, 1100000]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        
        # Load and validate
        provider = FileDataProvider(temp_data_dir)
        validator = DataValidator()
        
        historical = provider.fetch_historical_data(
            'VALID',
            datetime(2024, 1, 1),
            datetime(2024, 1, 2)
        )
        
        assert historical is not None
        
        # Validate each record
        for record in historical:
            is_valid, errors = validator.validate_record(record)
            assert is_valid, f"Validation errors: {errors}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
