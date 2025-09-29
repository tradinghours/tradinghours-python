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
        "base_url": "https://api.tradinghours.com/v3/",
        "store_dir": DEFAULT_STORE_DIR,
        "remote_dir": DEFAULT_STORE_DIR / "remote",
        "mode": "package"
    },
    "auth": {
        "token": "",
    },
    "package-mode": {
        "db_url": "",
        "table_prefix": "thstore_",
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

# Handle database URL - prioritize environment variable
db_url = os.getenv("TH_DB_URL", main_config.get("package-mode", "db_url", fallback=""))
main_config.set("package-mode", "db_url", db_url)



def print_help(text):
    """Print formatted help text."""
    lines = wrap(text, initial_indent="  ", subsequent_indent="  ")
    print("\n  --")
    print("\n".join(lines))
    print()


def _validate_server_mode_config():
    """
    Validate that server mode is not using custom package-mode settings.
    Server mode must use the default SQLite database.
    """    
    # Check for environment variable override
    if os.getenv("TH_DB_URL"):
        error_msg = "ERROR: Server mode cannot use the TH_DB_URL environment variable."
        help_msg = (
            "Server mode must use the default SQLite database. "
            "Please unset the TH_DB_URL environment variable when using server mode, "
            "or use package mode instead of server mode for custom database configurations."
        )
        print(error_msg)
        print_help(help_msg)
        sys.exit(1)
    
    # Get the current settings from the final config (after all processing)
    current_db_url = main_config.get("package-mode", "db_url")    
    current_table_prefix = main_config.get("package-mode", "table_prefix")
    default_table_prefix = default_settings["package-mode"]["table_prefix"]

    # Check if either setting has been customized from defaults
    custom_db = current_db_url != ""
    custom_prefix = current_table_prefix != default_table_prefix
    
    if custom_db or custom_prefix:
        error_msg = "ERROR: Server mode cannot use custom [package-mode] settings."
        help_msg = (
            "Server mode must use the default SQLite database. "
            "Please remove the [package-mode] section from your tradinghours.ini file when using server mode, "
            "or use package mode instead of server mode for custom database configurations."
        )
        
        print(error_msg)
        print_help(help_msg)
        sys.exit(1)


try:
    if sys.argv[1] == "serve":
        _validate_server_mode_config()
        main_config.set("internal", "mode", "server")
except IndexError:
    pass
