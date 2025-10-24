import os, sys
import configparser
import logging
import logging.config
from pathlib import Path
from textwrap import wrap
from typing import Optional, Dict, Any

from .exceptions import ConfigError

PROJECT_PATH = Path(__file__).parent
DEFAULT_STORE_DIR = PROJECT_PATH / "store_dir"
os.makedirs(DEFAULT_STORE_DIR, exist_ok=True)

# Define default settings in this dictionary
default_settings = {
    "internal": {
        "store_dir": DEFAULT_STORE_DIR,
        "remote_dir": DEFAULT_STORE_DIR / "remote",
        "mode": "package"
    },
    "data": {
        "token": "",
        "source": "https://api.tradinghours.com/v4/download",
        "aws_access_key_id": "",
        "aws_secret_access_key": "",
    },
    "server-mode": {
        "auto_import_frequency": 60 * 6, # in minutes; set to 0 to disable auto-import
        "allowed_hosts": "*",
        "allowed_origins": "*",
        "log_folder": "tradinghours_server_logs",
        "log_days_to_keep": 7,
        "log_level": "DEBUG",
    },
    "extra": {
        "check_tzdata": True,
    }
}

# Read config file with defaults
main_config = configparser.ConfigParser()
main_config.read_dict(default_settings)
main_config.read("tradinghours.ini")

# Handle data token - prioritize environment variable
token = os.getenv("TRADINGHOURS_TOKEN", main_config.get("data", "token", fallback=""))
main_config.set("data", "token", token)

try:
    assert main_config.getint("server-mode", "auto_import_frequency") >= 0
except (ValueError, AssertionError) as e:
    raise ConfigError(
        f"auto_import_frequency must be an integer >= 0 representing minutes. Set to 0 to disable auto-import."
    ) from e

def print_help(text):
    """Print formatted help text."""
    logger = get_logger(__name__)
    lines = wrap(text, initial_indent="  ", subsequent_indent="  ")
    logger.critical("\n  --")
    logger.critical("\n".join(lines))
    logger.critical()


try:
    if sys.argv[1] == "serve":
        main_config.set("internal", "mode", "server")
except IndexError:
    pass


class TradingHoursLoggingConfig:
    """Centralized logging configuration for TradingHours."""
    
    def __init__(self):
        self._configured = False
    
    def configure_logging(
        self, 
        mode: str = "package",
        log_level: Optional[str] = None,
        log_file: Optional[str] = None
    ) -> None:
        """Configure logging for the entire application."""
        if self._configured:
            return
            
        # Get configuration from main_config or parameters
        if log_level is None:
            if mode == "server":
                log_level = main_config.get("server-mode", "log_level", fallback="DEBUG")
            else:
                log_level = "INFO"
        
        if log_file is None and mode == "server":
            log_folder = main_config.get("server-mode", "log_folder", fallback="tradinghours_server_logs")
            log_file = Path(log_folder) / "th_server.log"
        
        # Configure dependency loggers first
        self._configure_dependency_loggers(log_level)
        
        # Configure main application logging
        config = self._get_logging_config(log_level, log_file)
        logging.config.dictConfig(config)
        
        self._configured = True
    
    def _configure_dependency_loggers(self, log_level: str) -> None:
        """Configure logging for third-party dependencies."""
        level = getattr(logging, log_level.upper())
        
        # Configure boto3 and AWS SDK logging
        boto3_loggers = [
            'boto3', 'botocore', 'boto3.resources', 'botocore.credentials',
            'botocore.utils', 'botocore.hooks', 'botocore.auth', 'botocore.parsers'
        ]
        for logger_name in boto3_loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
            # Remove existing handlers to avoid duplicate logs
            logger.handlers.clear()
            logger.propagate = True
            
    def _get_logging_config(self, log_level: str, log_file: Optional[str]) -> Dict[str, Any]:
        """Get logging configuration dictionary."""
        level = getattr(logging, log_level.upper())
        
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'detailed': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'simple': {
                    'format': '%(levelname)s: %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': level,
                    'formatter': 'simple',
                    'stream': 'ext://sys.stdout'
                }
            },
            'loggers': {
                'tradinghours': {
                    'level': level,
                    'handlers': ['console'],
                    'propagate': False
                },
                'th.server': {
                    'level': level,
                    'handlers': ['console'],
                    'propagate': False
                }
            },
            'root': {
                'level': level,
                'handlers': ['console']
            }
        }
        
        # Add file handler for server mode
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            config['handlers']['file'] = {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'level': level,
                'formatter': 'detailed',
                'filename': str(log_path),
                'when': 'midnight',
                'interval': 1,
                'backupCount': main_config.getint("server-mode", "log_days_to_keep", fallback=7),
                'encoding': 'utf-8',
                'suffix': '%Y-%m-%d'
            }
            config['loggers']['tradinghours']['handlers'].append('file')
            config['loggers']['th.server']['handlers'].append('file')
        
        return config
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance."""
        if not self._configured:
            # Auto-detect mode and configure
            mode = "server" if len(sys.argv) > 1 and sys.argv[1] == "serve" else "package"
            self.configure_logging(mode=mode)
        return logging.getLogger(name)


# Global instance
logging_config = TradingHoursLoggingConfig()

def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger."""
    return logging_config.get_logger(name)
