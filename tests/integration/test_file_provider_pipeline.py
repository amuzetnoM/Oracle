"""
Integration test for file-based data loading with full prediction pipeline.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from src.data_ingestion.providers.file_provider import FileDataProvider


class TestFileBasedPipeline:
    """Test complete pipeline using file-based data provider."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_stock_data(self, temp_data_dir):
        """Create realistic stock data for testing."""
        # Generate 100 days of realistic stock data
        np.random.seed(42)
        n_days = 100
        
        # Start at $100 and simulate random walk
        prices = [100.0]
        for _ in range(n_days - 1):
            change = np.random.randn() * 2  # Daily volatility
            prices.append(prices[-1] + change)
        
        prices = np.array(prices)
        
        # Create OHLCV data
        data = {
            'timestamp': pd.date_range('2024-01-01', periods=n_days, freq='D'),
            'open': prices + np.random.randn(n_days) * 0.5,
            'high': prices + np.abs(np.random.randn(n_days) * 1.0),
            'low': prices - np.abs(np.random.randn(n_days) * 1.0),
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, n_days).astype(float)
        }
        
        df = pd.DataFrame(data)
        
        # Save to CSV
        csv_path = Path(temp_data_dir) / "TEST.csv"
        df.to_csv(csv_path, index=False)
        
        return csv_path, df
    
    def test_file_provider_basic_functionality(self, temp_data_dir, sample_stock_data):
        """Test basic file provider functionality."""
        csv_path, df = sample_stock_data
        
        # Initialize provider
        provider = FileDataProvider(temp_data_dir)
        
        # Test current price
        current = provider.fetch_current_price('TEST')
        assert current is not None
        assert current['symbol'] == 'TEST'
        assert current['close'] == pytest.approx(df['close'].iloc[-1], rel=0.01)
        
        # Test historical data
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 4, 10)  # Get first 100 days
        
        historical = provider.fetch_historical_data('TEST', start_date, end_date)
        assert historical is not None
        assert len(historical) == 100
        
        # Verify data integrity
        for i, record in enumerate(historical):
            assert record['symbol'] == 'TEST'
            assert record['close'] == pytest.approx(df['close'].iloc[i], rel=0.01)
    
    def test_file_provider_with_feature_engineering(self, temp_data_dir, sample_stock_data):
        """Test file provider integration with feature engineering."""
        try:
            from src.feature_engineering import FeatureCalculator
        except ImportError:
            pytest.skip("FeatureCalculator not available")
        
        csv_path, df = sample_stock_data
        
        # Load data
        provider = FileDataProvider(temp_data_dir)
        historical = provider.fetch_historical_data(
            'TEST',
            datetime(2024, 1, 1),
            datetime(2024, 4, 10)
        )
        
        # Convert to format for feature calculation
        data = {
            'open': np.array([d['open'] for d in historical]),
            'high': np.array([d['high'] for d in historical]),
            'low': np.array([d['low'] for d in historical]),
            'close': np.array([d['close'] for d in historical]),
            'volume': np.array([d['volume'] for d in historical])
        }
        
        # Calculate features
        calculator = FeatureCalculator()
        features = calculator.calculate_all(data)
        
        # Verify features were calculated
        assert features is not None
        assert 'sma_20' in features
        assert 'rsi' in features
        assert len(features['sma_20']) > 0
    
    def test_multiple_symbols(self, temp_data_dir):
        """Test handling multiple symbols from files."""
        # Create multiple symbol files
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        for symbol in symbols:
            data = {
                'timestamp': pd.date_range('2024-01-01', periods=10),
                'close': np.random.uniform(100, 200, 10)
            }
            df = pd.DataFrame(data)
            df.to_csv(Path(temp_data_dir) / f"{symbol}.csv", index=False)
        
        # Initialize provider
        provider = FileDataProvider(temp_data_dir)
        
        # List symbols
        available = provider.list_available_symbols()
        assert len(available) == 3
        for symbol in symbols:
            assert symbol in available
        
        # Fetch data for each symbol
        for symbol in symbols:
            current = provider.fetch_current_price(symbol)
            assert current is not None
            assert current['symbol'] == symbol
    
    def test_file_formats_comparison(self, temp_data_dir):
        """Test that different file formats produce consistent results."""
        # Create same data in different formats
        data = {
            'timestamp': pd.date_range('2024-01-01', periods=10),
            'open': [100 + i for i in range(10)],
            'high': [102 + i for i in range(10)],
            'low': [98 + i for i in range(10)],
            'close': [101 + i for i in range(10)],
            'volume': [1000000 for i in range(10)]
        }
        df = pd.DataFrame(data)
        
        # Save as CSV
        df.to_csv(Path(temp_data_dir) / "CSV_TEST.csv", index=False)
        
        # Save as JSON
        df.to_json(Path(temp_data_dir) / "JSON_TEST.json", orient='records', date_format='iso')
        
        # Initialize provider
        provider = FileDataProvider(temp_data_dir)
        
        # Fetch from both
        csv_data = provider.fetch_current_price('CSV_TEST')
        json_data = provider.fetch_current_price('JSON_TEST')
        
        # Compare results
        assert csv_data is not None
        assert json_data is not None
        assert csv_data['close'] == json_data['close']
        assert csv_data['volume'] == json_data['volume']
    
    def test_date_range_filtering(self, temp_data_dir):
        """Test date range filtering works correctly."""
        # Create data spanning multiple months
        data = {
            'timestamp': pd.date_range('2024-01-01', periods=90),
            'close': np.random.uniform(100, 200, 90)
        }
        df = pd.DataFrame(data)
        df.to_csv(Path(temp_data_dir) / "RANGE_TEST.csv", index=False)
        
        provider = FileDataProvider(temp_data_dir)
        
        # Fetch January data
        jan_data = provider.fetch_historical_data(
            'RANGE_TEST',
            datetime(2024, 1, 1),
            datetime(2024, 1, 31)
        )
        
        # Fetch February data
        feb_data = provider.fetch_historical_data(
            'RANGE_TEST',
            datetime(2024, 2, 1),
            datetime(2024, 2, 29)
        )
        
        # Verify correct filtering
        assert len(jan_data) == 31
        assert len(feb_data) == 29
        
        # Verify no overlap
        jan_dates = {d['timestamp'].date() for d in jan_data}
        feb_dates = {d['timestamp'].date() for d in feb_data}
        assert len(jan_dates & feb_dates) == 0
    
    def test_error_handling(self, temp_data_dir):
        """Test error handling for various edge cases."""
        provider = FileDataProvider(temp_data_dir)
        
        # Non-existent symbol
        result = provider.fetch_current_price('NONEXISTENT')
        assert result is None
        
        # Empty symbol
        result = provider.fetch_current_price('')
        assert result is None
        
        # None symbol
        result = provider.fetch_current_price(None)
        assert result is None
    
    def test_data_validation_integration(self, temp_data_dir):
        """Test file provider with data validator."""
        from src.data_ingestion import DataValidator
        
        # Create valid data
        data = {
            'timestamp': pd.date_range('2024-01-01', periods=10),
            'open': [100 + i for i in range(10)],
            'high': [102 + i for i in range(10)],
            'low': [98 + i for i in range(10)],
            'close': [101 + i for i in range(10)],
            'volume': [1000000 for i in range(10)]
        }
        df = pd.DataFrame(data)
        df.to_csv(Path(temp_data_dir) / "VALID.csv", index=False)
        
        # Load and validate
        provider = FileDataProvider(temp_data_dir)
        validator = DataValidator()
        
        historical = provider.fetch_historical_data(
            'VALID',
            datetime(2024, 1, 1),
            datetime(2024, 1, 10)
        )
        
        # Validate all records
        valid_records, invalid_records = validator.validate_batch(historical)
        
        assert len(valid_records) == 10
        assert len(invalid_records) == 0
    
    def test_normalizer_integration(self, temp_data_dir):
        """Test file provider with data normalizer."""
        from src.data_ingestion import DataNormalizer
        
        # Create data
        data = {
            'timestamp': pd.date_range('2024-01-01', periods=5),
            'close': [100, 101, 102, 103, 104]
        }
        df = pd.DataFrame(data)
        df.to_csv(Path(temp_data_dir) / "NORM_TEST.csv", index=False)
        
        # Load data
        provider = FileDataProvider(temp_data_dir)
        historical = provider.fetch_historical_data(
            'NORM_TEST',
            datetime(2024, 1, 1),
            datetime(2024, 1, 5)
        )
        
        # Normalize data
        normalizer = DataNormalizer()
        normalized = normalizer.normalize_batch(historical, 'file')
        
        assert len(normalized) == 5
        for record in normalized:
            assert record['provider'] == 'file'
            assert 'timestamp' in record
            assert 'close' in record


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
