import configparser
import os
from pathlib import Path

PROJECT_PATH = Path(__file__).parent

# Define default settings in this dictionary
default_settings = {
    "api": {
        "token": os.getenv("TRADINGHOURS_TOKEN", ""),
        "base_url": "https://api.tradinghours.com/v3/",
    },
    "data": {
        "local_dir": PROJECT_PATH / "store_dir" / "local",
        "remote_dir": PROJECT_PATH / "store_dir" / "remote",
    },
}

# Read config file with defaults
main_config = configparser.ConfigParser()
main_config.read_dict(default_settings)
main_config.read("tradinghours.ini")
