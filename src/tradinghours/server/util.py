import logging
from logging.handlers import TimedRotatingFileHandler
import io
from pathlib import Path
from ..config import main_config


def add_log_handlers(logger: logging.Logger, formatter):
    log_folder = main_config.get("server-mode", "log_folder")
    log_level_str = main_config.get("server-mode", "log_level").upper()
    log_level = getattr(logging, log_level_str)
    log_days_to_keep = main_config.getint("server-mode", "log_days_to_keep")

    logs_path = Path(log_folder)
    logs_path.mkdir(parents=True, exist_ok=True)
    log_file_path = logs_path / "th_server.log"

    logger.setLevel(log_level)

    # Use TimedRotatingFileHandler for daily rotation
    file_handler = TimedRotatingFileHandler(
        filename=str(log_file_path),
        when='midnight',
        interval=1,
        backupCount=log_days_to_keep,
        encoding='utf-8'
    )
    # Set suffix for rotated files (YYYY-MM-DD format)
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)
    return logger


def setup_root_logger():
    """Configure logging based on tradinghours.ini settings."""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    add_log_handlers(root_logger, formatter)

    

class LogCapture(io.TextIOWrapper):
    """Custom stream to capture stdout/stderr and send to our logger."""
    def __init__(self, original_stream, logger_name):
        self.original_stream = original_stream
        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        add_log_handlers(self.logger, formatter)
        self.level_to_log = logging.INFO if logger_name == "stdout" else logging.ERROR

    def write(self, text):
        text = text.strip()
        if text:  # Only log non-empty lines
            self.logger.log(self.level_to_log, text)
        
    def flush(self):
        self.original_stream.flush()
        
    def isatty(self):
        """Check if the original stream is a TTY."""
        try:
            return self.original_stream.isatty()
        except (AttributeError, ValueError):
            return False

    def __getattr__(self, name):
        return getattr(self.original_stream, name)


