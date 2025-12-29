"""
Data Ingestion Module
Multi-source data providers for fetching market data
"""

from .base_provider import BaseProvider
from .normalizer import DataNormalizer

# Optional imports that may not be available in all environments
try:
    from .validator import DataValidator
    from .cache_manager import CacheManager
    __all__ = ['BaseProvider', 'DataNormalizer', 'DataValidator', 'CacheManager']
except ImportError:
    __all__ = ['BaseProvider', 'DataNormalizer']
