import zoneinfo

import pytest, json
from unittest.mock import MagicMock

import requests.exceptions
from requests.models import Response

from tradinghours.util import (StrEncoder,
                               slugify,
                               snake_case,
                               snake_dict,
                               _get_latest_tzdata_version,
                               check_if_tzdata_required_and_up_to_date)

from tradinghours.exceptions import MissingTzdata
import importlib.metadata as metadata


@pytest.mark.parametrize("name, expected", [
    ("Hello World", "hello-world"),
    ("Hello!@#$%^World", "hello-world"),
    ("Hello    World", "hello-world"),
])
def test_slugify(level, name, expected):
    assert slugify(name) == expected


@pytest.mark.parametrize("name, exception", [
    (None, ValueError),
    (123, TypeError),
])
def test_slugify_with_errors(level, name, exception):
    with pytest.raises(exception):
        slugify(name)


@pytest.mark.parametrize("text, expected", [
    ("hello-world", "hello_world"),
    ("helloWorld", "hello_world"),
    ("HELLO_WORLD", "hello_world"),
])
def test_snake_case(level, text, expected):
    assert snake_case(text) == expected


@pytest.mark.parametrize("text, exception", [
    (None, ValueError),
    (123, TypeError),
])
def test_snake_case_with_errors(level, text, exception):
    with pytest.raises(exception):
        snake_case(text)


def test_snake_dict(level):
    data = {"First Name": "John", "Last Name": "Doe", "Age": 30}
    expected = {"first_name": "John", "last_name": "Doe", "age": 30}
    assert snake_dict(data) == expected

def test_snake_dict_with_errors(level):
    with pytest.raises(TypeError):
        snake_dict("This is not a dictionary")

def test_str_encoder(level):
    data = {"name": "John", "age": 30}
    expected = '{"name": "John", "age": 30}'
    assert json.dumps(data, cls=StrEncoder) == expected

def test_str_encoder_non_serializable(level):
    data = {"name": "John", "age": 30, "non_serializable": set()}
    expected = '{"name": "John", "age": 30, "non_serializable": "set()"}'
    assert json.dumps(data, cls=StrEncoder) == expected


################
# TZDATA CHECK #
################

@pytest.fixture
def mock_requests_get(mocker):
    mock_response = MagicMock(spec=Response)
    mocker.patch("tradinghours.util.requests.get", return_value=mock_response)
    return mock_response

#############################
### _get_latest_version tests

def test_latest_version_success(mock_requests_get):
    mock_requests_get.status_code = 200
    mock_requests_get.json.return_value = {"info": {"version": "2021.1"}}
    assert _get_latest_tzdata_version() == "2021.1"

def test_latest_version_failure(mock_requests_get):
    mock_requests_get.status_code = 404
    assert _get_latest_tzdata_version() is None

    mock_requests_get.side_effect = requests.exceptions.ConnectionError
    assert _get_latest_tzdata_version() is None

    mock_requests_get.side_effect = requests.exceptions.Timeout
    assert _get_latest_tzdata_version() is None



#################################################
### check_if_tzdata_required_and_up_to_date tests

def test_check_tzdata_disbaled(mocker):
    mocker.patch("tradinghours.util.main_config.getboolean", return_value=False)
    assert check_if_tzdata_required_and_up_to_date() is False

def test_check_tzdata_not_required(mocker):
    mocker.patch("tradinghours.util.TZPATH", new=('/usr/share/zoneinfo',
                                         '/usr/lib/zoneinfo',
                                         '/usr/share/lib/zoneinfo',
                                         '/etc/zoneinfo'))
    mocker.patch("tradinghours.util.metadata.version", side_effect=metadata.PackageNotFoundError)
    assert check_if_tzdata_required_and_up_to_date() is True

def test_check_tzdata_required_and_missing(mocker):
    mocker.patch("tradinghours.util.main_config.getboolean", return_value=True)
    mocker.patch("tradinghours.util.TZPATH", new=tuple())
    mocker.patch("tradinghours.util.metadata.version", side_effect=metadata.PackageNotFoundError)
    with pytest.raises(MissingTzdata):
        check_if_tzdata_required_and_up_to_date()

def test_check_tzdata_required_and_outdated(mocker, mock_requests_get):
    mocker.patch("tradinghours.util.main_config.getboolean", return_value=True)
    mocker.patch("tradinghours.util.TZPATH", new=tuple())
    mocker.patch("tradinghours.util.metadata.version", return_value="2020.1")
    mock_requests_get.status_code = 200
    mock_requests_get.json.return_value = {"info": {"version": "2021.1"}}
    with pytest.warns(UserWarning, match="The installed version of tzdata is 2020.1"):
        assert check_if_tzdata_required_and_up_to_date() is None

def test_check_tzdata_required_and_up_to_date(mocker, mock_requests_get):
    mocker.patch("tradinghours.util.main_config.getboolean", return_value=True)
    mocker.patch("tradinghours.util.TZPATH", new=tuple())
    mocker.patch("tradinghours.util.metadata.version", return_value="2021.1")
    mock_requests_get.status_code = 200
    mock_requests_get.json.return_value = {"info": {"version": "2021.1"}}
    assert check_if_tzdata_required_and_up_to_date() is True


def test_check_tzdata_required_and_fail(mocker, mock_requests_get):
    mocker.patch("tradinghours.util.main_config.getboolean", return_value=True)
    mocker.patch("tradinghours.util.TZPATH", new=tuple())
    mocker.patch("tradinghours.util.metadata.version", return_value="2021.1")
    mock_requests_get.status_code = 500
    mock_requests_get.return_value = None
    with pytest.warns(UserWarning, match="Failed to get latest version of tzdata."):
        assert check_if_tzdata_required_and_up_to_date() is None


