"""
Configuration Loader
Loads and manages system configuration from YAML files and environment variables
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigLoader:
    """
    Central configuration management system.
    Loads configuration from YAML files and environment variables.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration loader.
        
        Args:
            config_dir: Path to configuration directory (defaults to project_root/config)
        """
        # Load environment variables
        load_dotenv()
        
        # Determine configuration directory
        if config_dir is None:
            project_root = Path(__file__).parent.parent
            config_dir = project_root / "config"
        self.config_dir = Path(config_dir)
        
        # Load configurations
        self._config: Dict[str, Any] = {}
        self._load_default_config()
        self._load_provider_config()
        self._override_from_env()
    
    def _load_default_config(self) -> None:
        """Load default system configuration."""
        config_file = self.config_dir / "default.yaml"
        if config_file.exists():
            with open(config_file, 'r') as f:
                self._config.update(yaml.safe_load(f) or {})
    
    def _load_provider_config(self) -> None:
        """Load data provider configuration."""
        config_file = self.config_dir / "providers.yaml"
        if config_file.exists():
            with open(config_file, 'r') as f:
                provider_config = yaml.safe_load(f) or {}
                self._config['providers'] = provider_config.get('providers', {})
                self._config['normalization'] = provider_config.get('normalization', {})
                self._config['validation'] = provider_config.get('validation', {})
    
    def _override_from_env(self) -> None:
        """Override configuration with environment variables."""
        # Database configuration
        db_type = os.getenv('DATABASE_TYPE')
        if db_type:
            self._config['database']['type'] = db_type
        
        db_path = os.getenv('DATABASE_PATH')
        if db_path:
            self._config['database']['sqlite']['path'] = db_path
        
        # Logging configuration
        log_level = os.getenv('LOG_LEVEL')
        if log_level:
            self._config['logging']['level'] = log_level
        
        # Cache configuration
        cache_ttl = os.getenv('CACHE_TTL')
        if cache_ttl:
            self._config['cache']['ttl'] = int(cache_ttl)
        
        # Web UI configuration
        web_host = os.getenv('WEB_HOST')
        if web_host:
            self._config['web_ui']['host'] = web_host
        
        web_port = os.getenv('WEB_PORT')
        if web_port:
            self._config['web_ui']['port'] = int(web_port)
        
        flask_secret = os.getenv('FLASK_SECRET_KEY')
        if flask_secret:
            self._config['web_ui']['secret_key'] = flask_secret
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Configuration key path (e.g., 'database.type')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as dictionary."""
        return self._config.copy()
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a data provider from environment.
        
        Args:
            provider: Provider name (fred, alphavantage, binance, etc.)
            
        Returns:
            API key or None if not found
        """
        env_var_map = {
            'fred': 'FRED_API_KEY',
            'alphavantage': 'ALPHAVANTAGE_API_KEY',
            'rapidapi': 'RAPIDAPI_KEY',
            'binance': 'BINANCE_API_KEY',
            'coingecko': 'COINGECKO_API_KEY'
        }
        
        env_var = env_var_map.get(provider.lower())
        if env_var:
            return os.getenv(env_var)
        
        return None
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """
        Get configuration for a specific data provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Provider configuration dictionary
        """
        return self._config.get('providers', {}).get(provider, {})


# Global configuration instance
_config_instance: Optional[ConfigLoader] = None


def get_config() -> ConfigLoader:
    """
    Get global configuration instance (singleton pattern).
    
    Returns:
        ConfigLoader instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader()
    return _config_instance


def reload_config() -> ConfigLoader:
    """
    Reload configuration (useful for testing or config updates).
    
    Returns:
        New ConfigLoader instance
    """
    global _config_instance
    _config_instance = ConfigLoader()
    return _config_instance
