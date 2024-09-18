import pytest, json
import csv

from tradinghours import Market

import pytest, datetime
from unittest.mock import MagicMock, patch
from urllib.request import HTTPError

from tradinghours import client
from tradinghours.exceptions import TokenError, ClientError

@pytest.fixture
def client_urlopen():
    client.TOKEN = "test_token"
    client.BASE_URL = "http://example.com"
    with patch("tradinghours.client.urlopen") as mock_urlopen:
        yield client, mock_urlopen

@pytest.fixture
def mocked_client():
    """Provide a client instance."""
    client.TOKEN = "test_token"
    client.BASE_URL = "http://example.com"
    return client

@pytest.fixture
def patch_response(mocker):
    """Patch response with specific content."""
    def _patch(content):
        content = content.encode("utf-8")
        class MockResponse:
            status = 200
            def read(self):
                return content
        return mocker.patch("tradinghours.client.get_response", return_value=MockResponse())
    return _patch

@pytest.fixture
def patch_response_error(mocker):
    """Patch response to raise an exception."""
    def _patch(exception):
        return mocker.patch("tradinghours.client.get_response", side_effect=exception)
    return _patch

@pytest.fixture
def patch_response_file(mocker):
    """Patch response with content from a file."""
    def _patch(file_path):
        with open(file_path, "rb") as file:
            content = file.read()
        return mocker.patch("tradinghours.client.get_response", return_value=[content, b""])
    return _patch

def test_urlopen_successful(client_urlopen):
    client, mock_urlopen = client_urlopen
    mock_urlopen.return_value = "foobar"

    response = client.get_response("/test")
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



def test_download_temporary_token_error(mocked_client, patch_response_error):
    patch_response_error(TokenError("Token is missing or invalid"))
    with pytest.raises(TokenError):
        client.download_zip_file("/test")

def test_download_temporary_client_error(mocked_client, patch_response_error):
    patch_response_error(ClientError("Error getting server response"))
    with pytest.raises(ClientError):
        client.download_zip_file("/test")

def test_remote_timestamp(patch_response):
    timestamp = "2023-10-27T12:00:00"
    patch_response("{" + f'"last_updated":"{timestamp}"' + "}")

    expected_datetime = datetime.datetime.fromisoformat(timestamp)
    assert client.get_remote_timestamp() == expected_datetime

##
# TODO: This was for the weird bug when rows were appended to csv files
#   see if it's worth keeping
# def test_no_duplicates():
#     collection = default_catalog.find_model_collection(Market)
#     cluster = collection.clusters.get("us")
#
#     market_file = MarketFile(default_data_manager.csv_dir)
#     market_file.ingest(default_catalog.store)
#     cluster.flush()
#
#     market_file.ingest(default_catalog.store)
#     cluster.flush()
#
#     keys = set()
#     with open(cluster.location, "r", encoding="utf-8", newline="") as file:
#         for row in csv.reader(file):
#             if row[0] in keys:
#                 pytest.fail("Data was duplicated")
#             keys.add(row[0])
#






