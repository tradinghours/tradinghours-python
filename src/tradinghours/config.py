import configparser
import os
from pathlib import Path

PROJECT_PATH = Path(__file__).parent
DEFAULT_STORE_DIR = PROJECT_PATH / "store_dir"
os.makedirs(DEFAULT_STORE_DIR, exist_ok=True)

# Define default settings in this dictionary
default_settings = {
    "internal": {
        "base_url": "https://api.tradinghours.com/v3/",
        "remote_dir": DEFAULT_STORE_DIR / "remote",
    },
    "package-mode": {
        "db_url": f"sqlite:///{DEFAULT_STORE_DIR / 'tradinghours.db'}",
        "table_prefix": "thstore_",
    },
    "server-mode": {
        "allowed_hosts": "*",
        "allowed_origins": "*"
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

