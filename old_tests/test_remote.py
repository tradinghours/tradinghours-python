import datetime
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.request import HTTPError

from tradinghours.exceptions import ClientError, TokenError
from tradinghours.remote import Client, DataManager, default_data_manager
from tradinghours.config import main_config

class TestClientResponse(unittest.TestCase):
    def setUp(self):
        self.client = Client(token="test_token", base_url="http://example.com")
        self.mock_urlopen = patch("tradinghours.remote.urlopen").start()

    def tearDown(self):
        patch.stopall()

    def test_urlopen_successful(self):
        self.mock_urlopen.return_value = "foobar"

        with self.client.get_response("/test") as response:
            self.assertEqual(response, "foobar")

    def test_urlopen_token_error(self):
        self.mock_urlopen.side_effect = HTTPError(
            "url", 401, "Unauthorized", None, None
        )

        with self.assertRaises(TokenError):
            with self.client.get_response("/test"):
                pass

    def test_urlopen_client_error(self):
        self.mock_urlopen.side_effect = HTTPError(
            "url", 500, "Server Error", None, None
        )

        with self.assertRaises(ClientError):
            with self.client.get_response("/test"):
                pass


class ClientTestCase(unittest.TestCase):
    @property
    def client(self):
        if not hasattr(self, "_client"):
            self._client = Client(token="test_token", base_url="http://example.com")
        return self._client

    def patchResponse(self, content):
        content = content.encode("utf-8")
        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.side_effect = [content, b""]
        mock_response.__enter__.return_value.__exit__.return_value = False
        patcher = patch(
            "tradinghours.remote.Client.get_response", return_value=mock_response
        )
        return patcher

    def patchResponseError(self, exception):
        mock_response = MagicMock()
        mock_response.__enter__.side_effect = exception
        patcher = patch(
            "tradinghours.remote.Client.get_response", return_value=mock_response
        )
        return patcher

    def patchResponseFile(self, file_path):
        with open(file_path, "rb") as file:
            content = file.read()

        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.side_effect = [content, b""]
        mock_response.__enter__.return_value.__exit__.return_value = False
        patcher = patch(
            "tradinghours.remote.Client.get_response", return_value=mock_response
        )
        return patcher


class TestClientJson(ClientTestCase):
    def test_get_json_successful(self):
        with self.patchResponse('{"key": "value"}'):
            data = self.client.get_json("/test")
            self.assertEqual(data, {"key": "value"})

    def test_get_json_token_error(self):
        with self.patchResponseError(TokenError("Token is missing or invalid")):
            with self.assertRaises(TokenError):
                self.client.get_json("/test")

    def test_get_json_client_error(self):
        with self.patchResponseError(ClientError("Error getting server response")):
            with self.assertRaises(ClientError):
                self.client.get_json("/test")


class TestClientDownload(ClientTestCase):
    def test_download_temporary_successful(self):
        with self.patchResponse('{"key": "value"}'):
            with self.client.download_temporary("/test") as temp_file:
                content = temp_file.read().decode("utf-8")
                self.assertEqual(content, '{"key": "value"}')

    def test_download_temporary_token_error(self):
        with self.patchResponseError(TokenError("Token is missing or invalid")):
            with self.assertRaises(TokenError):
                with self.client.download_temporary("/test"):
                    pass

    def test_download_temporary_client_error(self):
        with self.patchResponseError(ClientError("Error getting server response")):
            with self.assertRaises(ClientError):
                with self.client.download_temporary("/test"):
                    pass


# Define a custom function to use as a side effect
def custom_validate_instance_arg(arg_name, arg_value, expected_type):
    return arg_value


class TestDataManager(ClientTestCase):
    @property
    def manager(self):
        if not hasattr(self, "_manager"):
            self._manager = default_data_manager
        return self._manager

    @patch(
        "tradinghours.remote.validate_instance_arg",
        side_effect=custom_validate_instance_arg,
    )
    @patch("tradinghours.remote.default_client.get_json")
    def test_remote_timestamp(self, mock_get_json, mock_validate_instance_arg):
        timestamp = "2023-10-27T12:00:00"
        mock_get_json.return_value = {"last_updated": timestamp}
        expected_datetime = datetime.datetime.fromisoformat(timestamp)

        self.assertEqual(self.manager.remote_timestamp, expected_datetime)

    # def test_download(self):
    #     # with self.patchResponseFile(Path("old_tests/sample_data.zip")) as patcher:
    #     self.manager.download()
    #
    #     # patcher.stop()
