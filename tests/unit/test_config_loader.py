"""
Test Configuration Loader
"""

import pytest
from src.config_loader import ConfigLoader, get_config, reload_config


class TestConfigLoader:
    """Test configuration loading functionality."""
    
    def test_config_loader_initialization(self):
        """Test that config loader initializes correctly."""
        config = ConfigLoader()
        assert config is not None
        assert isinstance(config._config, dict)
    
    def test_load_default_config(self):
        """Test loading default configuration."""
        config = ConfigLoader()
        system_name = config.get('system.name')
        assert system_name == 'Syndicate'
    
    def test_load_provider_config(self):
        """Test loading provider configuration."""
        config = ConfigLoader()
        providers = config.get('providers')
        assert providers is not None
        assert 'fred' in providers
        assert 'yfinance' in providers
    
    def test_get_with_dot_notation(self):
        """Test getting config values with dot notation."""
        config = ConfigLoader()
        log_level = config.get('logging.level')
        assert log_level is not None
    
    def test_get_with_default(self):
        """Test getting config with default value."""
        config = ConfigLoader()
        value = config.get('nonexistent.key', 'default_value')
        assert value == 'default_value'
    
    def test_get_all(self):
        """Test getting all configuration."""
        config = ConfigLoader()
        all_config = config.get_all()
        assert isinstance(all_config, dict)
        assert 'system' in all_config
    
    def test_get_provider_config(self):
        """Test getting provider-specific configuration."""
        config = ConfigLoader()
        fred_config = config.get_provider_config('fred')
        assert isinstance(fred_config, dict)
    
    def test_singleton_pattern(self):
        """Test that get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2
    
    def test_reload_config(self):
        """Test config reload functionality."""
        config1 = get_config()
        config2 = reload_config()
        # Should be a new instance
        assert config2 is not config1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
