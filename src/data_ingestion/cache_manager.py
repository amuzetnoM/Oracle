"""
Cache Manager
Simple file-based cache for API responses with TTL support
"""

import pickle
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timedelta
import hashlib
from src.logger import get_logger
from src.config_loader import get_config


class CacheManager:
    """
    File-based cache with Time-To-Live (TTL) support.
    Helps reduce API calls and improves performance.
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache files (defaults to config value)
        """
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # Setup cache directory
        if cache_dir is None:
            cache_dir = self.config.get('cache.directory', 'data/cache')
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache configuration
        self.enabled = self.config.get('cache.enabled', True)
        self.default_ttl = self.config.get('cache.ttl', 300)  # 5 minutes
        self.max_size = self.config.get('cache.max_size', 1000)
        
        self.logger.info(f"Cache initialized at {self.cache_dir}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if not self.enabled:
            return None
        
        cache_file = self._get_cache_file(key)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Check if expired
            if datetime.now() > cache_data['expires_at']:
                self.logger.debug(f"Cache expired for key: {key}")
                cache_file.unlink()  # Delete expired cache
                return None
            
            self.logger.debug(f"Cache hit for key: {key}")
            return cache_data['value']
            
        except Exception as e:
            self.logger.warning(f"Cache read error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (defaults to config value)
            
        Returns:
            True if successfully cached, False otherwise
        """
        if not self.enabled:
            return False
        
        if ttl is None:
            ttl = self.default_ttl
        
        cache_file = self._get_cache_file(key)
        
        try:
            cache_data = {
                'value': value,
                'cached_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(seconds=ttl)
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            self.logger.debug(f"Cached key: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            self.logger.error(f"Cache write error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        cache_file = self._get_cache_file(key)
        
        if cache_file.exists():
            cache_file.unlink()
            self.logger.debug(f"Deleted cache key: {key}")
            return True
        
        return False
    
    def clear(self) -> int:
        """
        Clear all cache files.
        
        Returns:
            Number of files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob('*.cache'):
            cache_file.unlink()
            count += 1
        
        self.logger.info(f"Cleared {count} cache files")
        return count
    
    def clear_expired(self) -> int:
        """
        Clear only expired cache files.
        
        Returns:
            Number of expired files deleted
        """
        count = 0
        now = datetime.now()
        
        for cache_file in self.cache_dir.glob('*.cache'):
            try:
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                if now > cache_data['expires_at']:
                    cache_file.unlink()
                    count += 1
                    
            except Exception:
                # If we can't read it, delete it
                cache_file.unlink()
                count += 1
        
        if count > 0:
            self.logger.info(f"Cleared {count} expired cache files")
        
        return count
    
    def _get_cache_file(self, key: str) -> Path:
        """
        Get cache file path for a key.
        
        Args:
            key: Cache key
            
        Returns:
            Path to cache file
        """
        # Hash the key to create a safe filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def get_cache_size(self) -> int:
        """
        Get number of cached items.
        
        Returns:
            Number of cache files
        """
        return len(list(self.cache_dir.glob('*.cache')))
    
    def make_key(self, *args, **kwargs) -> str:
        """
        Create a cache key from arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        return ":".join(key_parts)
