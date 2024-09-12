import datetime
import json
import shutil
import tempfile
import zipfile
from contextlib import contextmanager
from functools import cached_property
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from .config import main_config
from .exceptions import ClientError, TokenError
from .typing import StrOrPath
from .validate import validate_instance_arg, validate_path_arg

TOKEN = main_config.get("api", "token")
BASE_URL = main_config.get("api", "base_url")
ROOT = Path(main_config.get("data", "remote_dir"))

@contextmanager
def get_response(path):
    url = urljoin(BASE_URL, path)
    request = Request(url)
    request.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        yield urlopen(request)
    except HTTPError as error:
        if error.code == 401:
            raise TokenError("Token is missing or invalid")
        raise ClientError("Error getting server response", inner=error)

@contextmanager
def download_temporary(path):
    with get_response(path) as response:
        with tempfile.NamedTemporaryFile() as temp_file:
            shutil.copyfileobj(response, temp_file)
            temp_file.flush()
            temp_file.seek(0)
            yield temp_file

def get_json(path):
    with get_response(path) as response:
        data = json.load(response)
    return data

def get_remote_timestamp() -> datetime.datetime:
    data = get_json("last-updated")
    last_updated = data["last_updated"]
    timestamp = datetime.datetime.fromisoformat(last_updated)
    return timestamp


def download():
    """
    Downloads zip file from tradinghours and unzips it into the
    folder set in main_config.data.remote_dir
    """
    ROOT.mkdir(parents=True, exist_ok=True)
    with download_temporary("download") as temp_file:
        with zipfile.ZipFile(temp_file, "r") as zip_ref:
            zip_ref.extractall(ROOT)

    # TODO: Check how this would be handled differently
    #  for table creation and setting of access_level
    for file in ("currencies.csv",
                 "currency-holidays.csv",
                 "holidays.csv",
                 "markets.csv",
                 "mic-mapping.csv",
                 "phases.csv",
                 "regional-holidays.csv",
                 "schedules.csv",
                 "season-definitions.csv"):

        if not (ROOT / "csv" / file).exists():
            open(ROOT / "csv" / file, "w").close()

