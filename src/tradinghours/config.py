import configparser
import os
from pathlib import Path

PROJECT_PATH = Path(__file__).parent
DEFAULT_STORE_DIR = PROJECT_PATH / "store_dir"
os.makedirs(DEFAULT_STORE_DIR, exist_ok=True)

# Define default settings in this dictionary
default_settings = {
    "api": {
        "base_url": "https://api.tradinghours.com/v3/",
    },
    "data": {
        "remote_dir": DEFAULT_STORE_DIR / "remote",
        "db_url": f"sqlite:///{DEFAULT_STORE_DIR / 'tradinghours.db'}",
        "table_prefix": "thstore_"
    },
    "control": {
        "check_tzdata": True,
    }
}

# Read config file with defaults
main_config = configparser.ConfigParser()
main_config.read_dict(default_settings)
main_config.read("tradinghours.ini")

token = os.getenv("TRADINGHOURS_TOKEN", main_config.get("api", "token", fallback=""))
main_config.set("api", "token", token)
db_url = os.getenv("TH_DB_URL", main_config.get("data", "db_url", fallback=""))
main_config.set("data", "db_url", db_url)
