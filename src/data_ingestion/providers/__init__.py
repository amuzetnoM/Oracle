"""
Data Providers Package
Individual provider implementations
"""

from .file_provider import FileDataProvider

# Optional providers - only import if dependencies available
try:
    from .yfinance_provider import YFinanceProvider
    __all__ = ['FileDataProvider', 'YFinanceProvider']
except ImportError:
    __all__ = ['FileDataProvider']
