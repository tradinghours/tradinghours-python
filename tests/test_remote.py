import pytest
import csv

from tradinghours.catalog import default_catalog, default_data_manager, MarketFile
from tradinghours.models.market import Market

import pytest, datetime
from unittest.mock import MagicMock, patch
from urllib.request import HTTPError

from tradinghours.remote import Client, default_data_manager
from tradinghours.exceptions import TokenError, ClientError

@pytest.fixture
def client_urlopen():
    client = Client(token="test_token", base_url="http://example.com")
    with patch("tradinghours.remote.urlopen") as mock_urlopen:
        yield client, mock_urlopen

@pytest.fixture
def client():
    """Provide a client instance."""
    return Client(token="test_token", base_url="http://example.com")

@pytest.fixture
def patch_response(mocker):
    """Patch response with specific content."""
    def _patch(content):
        mock_response = MagicMock()
        content = content.encode("utf-8")
        mock_response.__enter__.return_value.read.side_effect = [content, b""]
        mock_response.__enter__.return_value.__exit__.return_value = False
        return mocker.patch("tradinghours.remote.Client.get_response", return_value=mock_response)
    return _patch

@pytest.fixture
def patch_response_error(mocker):
    """Patch response to raise an exception."""
    def _patch(exception):
        mock_response = MagicMock()
        mock_response.__enter__.side_effect = exception
        return mocker.patch("tradinghours.remote.Client.get_response", return_value=mock_response)
    return _patch

@pytest.fixture
def patch_response_file(mocker):
    """Patch response with content from a file."""
    def _patch(file_path):
        with open(file_path, "rb") as file:
            content = file.read()
        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.side_effect = [content, b""]
        mock_response.__enter__.return_value.__exit__.return_value = False
        return mocker.patch("tradinghours.remote.Client.get_response", return_value=mock_response)
    return _patch

def test_urlopen_successful(client_urlopen):
    client, mock_urlopen = client_urlopen
    mock_urlopen.return_value = "foobar"

    with client.get_response("/test") as response:
        assert response == "foobar"

def test_urlopen_token_error(client_urlopen):
    client, mock_urlopen = client_urlopen
    mock_urlopen.side_effect = HTTPError("url", 401, "Unauthorized", None, None)

    with pytest.raises(TokenError):
        with client.get_response("/test"):
            pass

def test_urlopen_client_error(client_urlopen):
    client, mock_urlopen = client_urlopen
    mock_urlopen.side_effect = HTTPError("url", 500, "Server Error", None, None)

    with pytest.raises(ClientError):
        with client.get_response("/test"):
            pass


def test_get_json_successful(client, patch_response):
    patch_response('{"key": "value"}')
    data = client.get_json("/test")
    assert data == {"key": "value"}

def test_get_json_token_error(client, patch_response_error):
    patch_response_error(TokenError("Token is missing or invalid"))
    with pytest.raises(TokenError):
        client.get_json("/test")

def test_get_json_client_error(client, patch_response_error):
    patch_response_error(ClientError("Error getting server response"))
    with pytest.raises(ClientError):
        client.get_json("/test")

def test_download_temporary_successful(client, patch_response):
    patch_response('{"key": "value"}')
    with client.download_temporary("/test") as temp_file:
        content = temp_file.read().decode("utf-8")
        assert content == '{"key": "value"}'

def test_download_temporary_token_error(client, patch_response_error):
    patch_response_error(TokenError("Token is missing or invalid"))
    with pytest.raises(TokenError):
        with client.download_temporary("/test"):
            pass

def test_download_temporary_client_error(client, patch_response_error):
    patch_response_error(ClientError("Error getting server response"))
    with pytest.raises(ClientError):
        with client.download_temporary("/test"):
            pass


def test_remote_timestamp(mocker):
    timestamp = "2023-10-27T12:00:00"
    mocker.patch("tradinghours.remote.default_client.get_json", return_value={"last_updated": timestamp})

    expected_datetime = datetime.datetime.fromisoformat(timestamp)
    assert default_data_manager.remote_timestamp == expected_datetime


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







