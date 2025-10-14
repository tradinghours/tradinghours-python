import os, sys
import configparser
from pathlib import Path
from textwrap import wrap

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
        "allowed_hosts": "*",
        "allowed_origins": "*",
        "log_folder": "tradinghours_server_logs",
        "log_days_to_keep": 7,
        "log_level": "DEBUG",
        "uvicorn_workers": 1,
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
