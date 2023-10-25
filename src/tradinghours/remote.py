import datetime
import json
import os
import shutil
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path
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
        self.client = client
        self.root = root

    def fetch_last_updated(self) -> datetime.datetime:
        data = default_client.get_json("last-updated")
        last_updated_str = data["last_updated"]
        last_updated = datetime.datetime.fromisoformat(last_updated_str)
        return last_updated

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


if __name__ == "__main__":
    last_updated = default_data_manager.fetch_last_updated()
    print("Remote Last Updated", last_updated)
