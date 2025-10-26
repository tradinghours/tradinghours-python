import os, sys
import configparser
import logging
import logging.config
from pathlib import Path
from textwrap import wrap
from typing import Optional, Dict, Any

from .exceptions import ConfigError


class TimedRotatingFileHandlerWithSuffix(logging.handlers.TimedRotatingFileHandler):
    """TimedRotatingFileHandler that sets suffix after initialization."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.suffix = "%Y-%m-%d"


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
        "log_level": "INFO",
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
            
        mode = main_config.get("internal", "mode")        
        if mode == "package":
            self._configure_package_mode()
        elif mode == "server":
            self._configure_server_mode(log_level, log_file)
        else:
            raise ConfigError(f"Invalid logging mode: {mode}")
        
        self._configured = True
    
    def _configure_package_mode(self) -> None:
        """Configure logging for package mode."""
        # Clear all existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Configure formatters
        formatters = {
            'simple': {
                'format': '%(message)s'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        }
        
        # Configure handlers
        handlers = {
            'stdout': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'simple',
                'stream': 'ext://sys.stdout'
            },
            'debug_file': {
                'class': 'logging.FileHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'filename': 'debug.txt',
                'mode': 'w',
                'encoding': 'utf-8'
            }
        }
        
        # Configure loggers
        loggers = {
            'tradinghours': {
                'level': 'INFO',
                'handlers': ['stdout', 'debug_file'],
                'propagate': False
            }
        }
        
        for dep_name in logging.Logger.manager.loggerDict:
            if dep_name.startswith("tradinghours"):
                continue
            loggers[dep_name] = {
                'level': 'WARNING',
                'handlers': ['debug_file'],
                'propagate': False
            }
        
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': formatters,
            'handlers': handlers,
            'loggers': loggers
        }
        
        logging.config.dictConfig(config)
    
    def _configure_server_mode(self, log_level: Optional[str], log_file: Optional[str]) -> None:
        """Configure logging for server mode."""
        # Get configuration from main_config or parameters
        if log_level is None:
            log_level = main_config.get("server-mode", "log_level", fallback="DEBUG")
        
        if log_file is None:
            log_folder = main_config.get("server-mode", "log_folder", fallback="tradinghours_server_logs")
            log_file = Path(log_folder) / "th_server.log"
        
        level = getattr(logging, log_level.upper())
        
        # Clear all existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Configure formatters
        formatters = {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        }
        
        # Configure handlers
        handlers = {
            'console': {
                'class': 'logging.StreamHandler',
                'level': level,
                'formatter': 'detailed',
                'stream': 'ext://sys.stdout'
            }
        }
        
        # Build list of handler names for root logger
        handler_names = ['console']
        
        # Add file handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            handlers['file'] = {
                '()': TimedRotatingFileHandlerWithSuffix,
                'level': level,
                'formatter': 'detailed',
                'filename': str(log_path),
                'when': 'midnight',
                'interval': 1,
                'backupCount': main_config.getint("server-mode", "log_days_to_keep", fallback=7),
                'encoding': 'utf-8'
            }
            handler_names.append('file')
        
        # Configure root logger to handle all loggers (tradinghours.* and dependencies)
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': formatters,
            'handlers': handlers,
            'root': {
                'level': level,
                'handlers': handler_names
            }
        }
        
        logging.config.dictConfig(config)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance."""
        if not self._configured:
            # Auto-detect mode and configure
            mode = "server" if len(sys.argv) > 1 and sys.argv[1] == "serve" else "package"
            self.configure_logging(mode=mode)
        return logging.getLogger(name)
    


# Global instance
logging_config = TradingHoursLoggingConfig()
logging_config.configure_logging()

def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger."""
    return logging_config.get_logger(name)
