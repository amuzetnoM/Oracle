"""
Yahoo Finance Provider
Uses yfinance library to fetch market data from Yahoo Finance
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import yfinance as yf
from src.data_ingestion.base_provider import BaseProvider
from src.data_ingestion.cache_manager import CacheManager


class YFinanceProvider(BaseProvider):
    """
    Yahoo Finance data provider using yfinance library.
    Supports stocks, ETFs, indices, forex, and cryptocurrencies.
    """
    
    def __init__(self):
        """Initialize Yahoo Finance provider."""
        super().__init__('yfinance')
        self.cache = CacheManager()
        self.default_interval = self.provider_config.get('default_interval', '1d')
    
    def fetch_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch current price for a symbol.
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'BTC-USD')
            
        Returns:
            Dictionary with timestamp, symbol, price, volume
        """
        if not self.validate_symbol(symbol):
            self.logger.error(f"Invalid symbol: {symbol}")
            return None
        
        # Check cache first
        cache_key = self.cache.make_key('yfinance', 'current', symbol)
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            self._rate_limit_check()
            
            # Fetch ticker data
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get last price from intraday data
            hist = ticker.history(period='1d', interval='1m')
            
            if hist.empty:
                self.logger.warning(f"No data available for {symbol}")
                return None
            
            latest = hist.iloc[-1]
            
            result = {
                'timestamp': latest.name.to_pydatetime(),
                'symbol': symbol.upper(),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'close': float(latest['Close']),
                'volume': float(latest['Volume'])
            }
            
            # Cache for 1 minute
            self.cache.set(cache_key, result, ttl=60)
            
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
        Fetch historical price data.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            
        Returns:
            List of OHLCV data dictionaries
        """
        if not self.validate_symbol(symbol):
            self.logger.error(f"Invalid symbol: {symbol}")
            return None
        
        # Check cache
        cache_key = self.cache.make_key(
            'yfinance', 'historical', symbol, 
            start_date.isoformat(), end_date.isoformat(), interval
        )
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            self._rate_limit_check()
            
            # Fetch historical data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval
            )
            
            if hist.empty:
                self.logger.warning(
                    f"No historical data for {symbol} from {start_date} to {end_date}"
                )
                return None
            
            # Convert to list of dictionaries
            result = []
            for timestamp, row in hist.iterrows():
                data_point = {
                    'timestamp': timestamp.to_pydatetime(),
                    'symbol': symbol.upper(),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': float(row['Volume'])
                }
                result.append(data_point)
            
            # Cache for 5 minutes (historical data doesn't change frequently)
            self.cache.set(cache_key, result, ttl=300)
            
            self.logger.info(
                f"Fetched {len(result)} historical records for {symbol}"
            )
            return result
            
        except Exception as e:
            self._handle_error(e, f"fetching historical data for {symbol}")
            return None
    
    def get_ticker_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get general information about a ticker.
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            Dictionary with ticker information
        """
        if not self.validate_symbol(symbol):
            return None
        
        try:
            self._rate_limit_check()
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol.upper(),
                'name': info.get('longName', info.get('shortName', '')),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap'),
                'currency': info.get('currency', 'USD')
            }
            
        except Exception as e:
            self._handle_error(e, f"fetching info for {symbol}")
            return None
