"""
Logging Infrastructure
Centralized logging system for Syndicate
"""

import logging
import logging.handlers
from pathlib import Path
from src.config_loader import get_config


class SyndicateLogger:
    """
    Centralized logging system with file and console output.
    """
    
    _loggers = {}
    _initialized = False
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize logging system with configuration."""
        if cls._initialized:
            return
        
        config = get_config()
        
        # Create logs directory
        log_file = config.get('logging.file', 'logs/syndicate.log')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Get logging configuration
        log_level = config.get('logging.level', 'INFO')
        log_format = config.get('logging.format', 
                                '[%(asctime)s] %(levelname)s [%(name)s] %(message)s')
        max_bytes = config.get('logging.max_bytes', 10485760)  # 10MB
        backup_count = config.get('logging.backup_count', 5)
        console_output = config.get('logging.console_output', True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(log_format)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, log_level.upper()))
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance for a module.
        
        Args:
            name: Logger name (typically __name__ of the module)
            
        Returns:
            Logger instance
        """
        if not cls._initialized:
            cls.initialize()
        
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        
        return cls._loggers[name]


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return SyndicateLogger.get_logger(name)
