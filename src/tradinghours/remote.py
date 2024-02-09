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


class Client:
    """TradingHours API client"""

    def __init__(self, token, base_url):
        self.token = token
        self.base_url = base_url

    @contextmanager
    def get_response(self, path):
        url = urljoin(self.base_url, path)
        request = Request(url)
        request.add_header("Authorization", f"Bearer {self.token}")
        try:
            yield urlopen(request)
        except HTTPError as error:
            if error.code == 401:
                raise TokenError("Token is missing or invalid")
            raise ClientError("Error getting server response", inner=error)

    @contextmanager
    def download_temporary(self, path):
        with self.get_response(path) as response:
            with tempfile.NamedTemporaryFile() as temp_file:
                shutil.copyfileobj(response, temp_file)
                temp_file.flush()
                temp_file.seek(0)
                yield temp_file

    def get_json(self, path):
        with self.get_response(path) as response:
            data = json.load(response)
        return data


class DataManager:
    """Manages accessing remote data"""

    def __init__(self, client: Client, root: StrOrPath):
        self.client = validate_instance_arg("client", client, Client)
        self._root = validate_path_arg("root", root)

    @property
    def root(self) -> Path:
        return self._root

    @property
    def csv_dir(self) -> Path:
        return self.root / "csv"

    @cached_property
    def remote_timestamp(self) -> datetime.datetime:
        data = default_client.get_json("last-updated")
        last_updated = data["last_updated"]
        timestamp = datetime.datetime.fromisoformat(last_updated)
        return timestamp

    @cached_property
    def local_timestamp(self) -> Optional[datetime.datetime]:
        version_file = self.root / "VERSION.txt"
        if version_file.exists():
            timestamp_format = "Generated at %a, %d %b %Y %H:%M:%S %z"
            content = version_file.read_text()
            line = content.splitlines()[0]
            timestamp = datetime.datetime.strptime(line, timestamp_format)
            return timestamp
        return None

    @cached_property
    def needs_download(self) -> bool:
        if self.local_timestamp:
            return self.remote_timestamp > self.local_timestamp
        return True

    def download(self):
        self.root.mkdir(parents=True, exist_ok=True)
        with default_client.download_temporary("download") as temp_file:
            with zipfile.ZipFile(temp_file, "r") as zip_ref:
                zip_ref.extractall(self.root)

        for file in ("currencies.csv",
                     "currency-holidays.csv",
                     "holidays.csv",
                     "markets.csv",
                     "mic-mapping.csv",
                     "phases.csv",
                     "regional-holidays.csv",
                     "schedules.csv",
                     "season-definitions.csv"):

            if not (self.csv_dir/file).exists():
                open(self.csv_dir/file, "w").close()


default_client = Client(
    main_config.get("api", "token"),
    main_config.get("api", "base_url"),
)

default_data_manager = DataManager(
    default_client,
    main_config.get("data", "remote_dir"),
)
