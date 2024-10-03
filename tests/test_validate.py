import pytest
import datetime as dt
import tradinghours.validate as val

def test_validate_date_arg():
    with pytest.raises(ValueError):
        val.validate_date_arg("test", None)

    with pytest.raises(TypeError):
        val.validate_date_arg("test", dt.datetime.now())

    with pytest.raises(ValueError):
        val.validate_date_arg("test", "2024-01-01 00:00:00")

    with pytest.raises(ValueError):
        val.validate_date_arg("test", "sdgssdg")

    date = dt.date.fromisoformat("2024-01-01")
    assert date == val.validate_date_arg("test", date)
    assert date == val.validate_date_arg("test", "2024-01-01")


def test_validate_range_args():
    with pytest.raises(ValueError):
        val.validate_range_args(2, 1)

    assert val.validate_range_args(1, 1) == (1, 1)

    assert val.validate_range_args(1, 2) == (1, 2)


def test_validate_mic_arg():
    with pytest.raises(ValueError):
        val.validate_mic_arg(None)

    with pytest.raises(TypeError):
        val.validate_mic_arg(123)

    with pytest.raises(ValueError):
        val.validate_mic_arg("12345")

    with pytest.raises(ValueError):
        val.validate_mic_arg("US.YE")

    assert val.validate_mic_arg("nyse") == "NYSE"
    assert val.validate_mic_arg("12Me") == "12ME"


