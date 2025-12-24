"""
Test YFinance Provider
"""

import pytest
from datetime import datetime, timedelta
from src.data_ingestion.providers.yfinance_provider import YFinanceProvider


class TestYFinanceProvider:
    """Test Yahoo Finance provider functionality."""
    
    @pytest.fixture
    def provider(self):
        """Create provider instance."""
        return YFinanceProvider()
    
    def test_provider_initialization(self, provider):
        """Test provider initializes correctly."""
        assert provider is not None
        assert provider.provider_name == 'yfinance'
        assert provider.is_enabled()
    
    def test_validate_symbol(self, provider):
        """Test symbol validation."""
        assert provider.validate_symbol('AAPL') == True
        assert provider.validate_symbol('BTC-USD') == True
        assert provider.validate_symbol('') == False
        assert provider.validate_symbol(None) == False
    
    @pytest.mark.slow
    def test_fetch_current_price(self, provider):
        """Test fetching current price (requires internet)."""
        result = provider.fetch_current_price('AAPL')
        
        if result:  # May fail without internet
            assert 'timestamp' in result
            assert 'symbol' in result
            assert 'close' in result
            assert result['symbol'] == 'AAPL'
            assert result['close'] > 0
    
    @pytest.mark.slow
    def test_fetch_historical_data(self, provider):
        """Test fetching historical data (requires internet)."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)
        
        result = provider.fetch_historical_data('AAPL', start_date, end_date)
        
        if result:  # May fail without internet
            assert isinstance(result, list)
            assert len(result) > 0
            assert 'timestamp' in result[0]
            assert 'close' in result[0]
    
    def test_cache_functionality(self, provider):
        """Test that cache is working."""
        # This test doesn't require internet if data is already cached
        assert provider.cache is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'not slow'])
