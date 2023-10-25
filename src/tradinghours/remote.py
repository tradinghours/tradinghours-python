import datetime
import json
import os
import shutil
import tempfile
import zipfile
from contextlib import contextmanager
from functools import cached_property
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin
from urllib.request import Request, urlopen

BASE_URL = "https://api.tradinghours.com/v3/"


class ClientError(Exception):
    pass


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
        with urlopen(request) as response:
            if response.getcode() != 200:
                raise ClientError("Unexpected HTTP status")
            yield response

    @contextmanager
    def download_temporary(self, path):
        with self.get_response(path) as response:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                shutil.copyfileobj(response, temp_file)
                yield temp_file

    def get_json(self, path):
        with self.get_response(path) as response:
            data = json.load(response)
        return data


class DataManager:
    """Manages accessing remote data"""

    def __init__(self, client, root):
        self.client: Client = client
        self.root: Path = root

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
        return self.remote_timestamp > self.local_timestamp

    def download(self):
        self.root.mkdir(parents=True, exist_ok=True)
        with default_client.download_temporary("download") as temp_file:
            with zipfile.ZipFile(temp_file.name, "r") as zip_ref:
                zip_ref.extractall(self.root)


default_client = Client(os.getenv("TRADINGHOURS_TOKEN"), BASE_URL)

default_data_manager = DataManager(
    default_client,
    Path(__file__).parent / "store_dir" / "remote",
)
