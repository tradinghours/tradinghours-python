import pytest
import csv

from tradinghours.catalog import default_catalog, default_data_manager, MarketFile
from tradinghours.models.market import Market

import pytest
from unittest.mock import patch
from urllib.request import HTTPError


from tradinghours.remote import Client
from tradinghours.exceptions import TokenError, ClientError

@pytest.fixture
def client():
    client = Client(token="test_token", base_url="http://example.com")
    with patch("tradinghours.remote.urlopen") as mock_urlopen:
        yield client, mock_urlopen

def test_urlopen_successful(client):
    client, mock_urlopen = client
    mock_urlopen.return_value = "foobar"

    with client.get_response("/test") as response:
        assert response == "foobar"

def test_urlopen_token_error(client):
    client, mock_urlopen = client
    mock_urlopen.side_effect = HTTPError("url", 401, "Unauthorized", None, None)

    with pytest.raises(TokenError):
        with client.get_response("/test"):
            pass

def test_urlopen_client_error(client):
    client, mock_urlopen = client
    mock_urlopen.side_effect = HTTPError("url", 500, "Server Error", None, None)

    with pytest.raises(ClientError):
        with client.get_response("/test"):
            pass



def test_no_duplicates(level):
    collection = default_catalog.find_model_collection(Market)
    cluster = collection.clusters.get("us")

    market_file = MarketFile(default_data_manager.csv_dir)
    market_file.ingest(default_catalog.store)
    cluster.flush()

    market_file.ingest(default_catalog.store)
    cluster.flush()

    keys = set()
    with open(cluster.location, "r", encoding="utf-8", newline="") as file:
        for row in csv.reader(file):
            if row[0] in keys:
                pytest.fail("Data was duplicated")
            keys.add(row[0])







