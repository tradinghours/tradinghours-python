import os, sys
import configparser
from pathlib import Path
from textwrap import wrap

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
    "auth": {
        "token": "",
    },
    "data": {
        "source": "https://api.tradinghours.com/v4/download",
    },
    "server-mode": {
        "auto_import_frequency": 60 * 6, # minutes; set to 0 to disable auto-import
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

# Handle auth token - prioritize environment variable
token = os.getenv("TRADINGHOURS_TOKEN", main_config.get("auth", "token", fallback=""))
main_config.set("auth", "token", token)

try:
    assert main_config.getint("server-mode", "auto_import_frequency") >= 0
except (ValueError, AssertionError) as e:
    raise ConfigError(
        f"auto_import_frequency must be an integer >= 0 representing minutes. Set to 0 to disable auto-import."
    ) from e

def print_help(text):
    """Print formatted help text."""
    lines = wrap(text, initial_indent="  ", subsequent_indent="  ")
    print("\n  --")
    print("\n".join(lines))
    print()


try:
    if sys.argv[1] == "serve":
        main_config.set("internal", "mode", "server")
except IndexError:
    pass
