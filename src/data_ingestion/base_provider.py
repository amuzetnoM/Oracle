"""
Base Provider Interface
Abstract base class for all data providers
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
from src.logger import get_logger
from src.config_loader import get_config


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_calls: int, period: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed per period
            period: Time period in seconds (default: 60)
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.logger = get_logger(__name__)
    
    def wait_if_needed(self) -> None:
        """Wait if rate limit would be exceeded."""
        now = time.time()
        
        # Remove calls outside the current period
        self.calls = [call_time for call_time in self.calls 
                      if now - call_time < self.period]
        
        if len(self.calls) >= self.max_calls:
            # Calculate wait time
            oldest_call = min(self.calls)
            wait_time = self.period - (now - oldest_call) + 1
            
            if wait_time > 0:
                self.logger.warning(
                    f"Rate limit reached. Waiting {wait_time:.2f} seconds..."
                )
                time.sleep(wait_time)
                self.calls = []
        
        self.calls.append(time.time())


class BaseProvider(ABC):
    """
    Abstract base class for all data providers.
    
    All providers must implement the fetch methods and follow
    a consistent interface for data retrieval.
    """
    
    def __init__(self, provider_name: str):
        """
        Initialize base provider.
        
        Args:
            provider_name: Name of the provider (e.g., 'fred', 'yfinance')
        """
        self.provider_name = provider_name
        self.logger = get_logger(f"provider.{provider_name}")
        self.config = get_config()
        
        # Load provider configuration
        self.provider_config = self.config.get_provider_config(provider_name)
        self.enabled = self.provider_config.get('enabled', True)
        
        # Setup rate limiter
        rate_limit = self.provider_config.get('rate_limit', 60)
        self.rate_limiter = RateLimiter(rate_limit)
        
        # Timeout configuration
        self.timeout = self.provider_config.get('timeout', 30)
        
        self.logger.info(f"Initialized {provider_name} provider")
    
    @abstractmethod
    def fetch_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch current price for a symbol.
        
        Args:
            symbol: Ticker symbol or asset identifier
            
        Returns:
            Dictionary with keys: timestamp, symbol, price, volume
            None if fetch fails
        """
        pass
    
    @abstractmethod
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
            symbol: Ticker symbol or asset identifier
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval (e.g., '1d', '1h', '5m')
            
        Returns:
            List of dictionaries with OHLCV data
            None if fetch fails
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if provider is enabled."""
        return self.enabled
    
    def get_name(self) -> str:
        """Get provider name."""
        return self.provider_name
    
    def _rate_limit_check(self) -> None:
        """Check and enforce rate limits."""
        if self.enabled:
            self.rate_limiter.wait_if_needed()
    
    def _handle_error(self, error: Exception, context: str = "") -> None:
        """
        Handle and log errors consistently.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
        """
        error_msg = f"{self.provider_name} error"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        
        self.logger.error(error_msg)
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate symbol format.
        
        Args:
            symbol: Symbol to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not symbol or not isinstance(symbol, str):
            return False
        
        # Basic validation - alphanumeric and some special chars
        return len(symbol) > 0 and len(symbol) < 20
    
    def __repr__(self) -> str:
        """String representation of provider."""
        status = "enabled" if self.enabled else "disabled"
        return f"{self.provider_name.upper()} Provider ({status})"
