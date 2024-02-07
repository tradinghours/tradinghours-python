import pytest
import pytz
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

# Assume we have a function `convert_to_timezone` that converts given naive datetime to the specified timezone
# from yourmodule import convert_to_timezone

# def make_timezone_obj(tz):
#     return pytz.timezone(tz)
#
# def convert_to_timezone(naive_dt, timezone_str):
#     tz_obj = make_timezone_obj(timezone_str)
#     return tz_obj.localize(naive_dt)
#

def make_timezone_obj(tz):
    return ZoneInfo(tz)

def convert_to_timezone(naive_dt, timezone_str):
    tz_obj = make_timezone_obj(timezone_str)
    return naive_dt.replace(tzinfo=tz_obj)


#
# @pytest.mark.parametrize("naive_dt, timezone_str, expected_dt", [
#     # Test DST start transition (US/Eastern, 2nd Sunday in March)
#     (datetime(2022, 3, 13, 2), "US/Eastern", convert_to_timezone(datetime(2022, 3, 13, 3), "US/Eastern")),
#     # Test DST end transition (US/Eastern, 1st Sunday in November)
#     (datetime(2022, 11, 6, 1), "US/Eastern", convert_to_timezone(datetime(2022, 11, 6, 1), "US/Eastern")),
# ])
# def test_dst_transitions(naive_dt, timezone_str, expected_dt):
#     converted = convert_to_timezone(naive_dt, timezone_str)
#     print(converted, expected_dt, converted == expected_dt)
#     assert converted == expected_dt, str(converted) + "==" + str(expected_dt)

@pytest.mark.parametrize("dt, days, expected_dt", [
    # Adding days over a leap day (non-leap year)
    (convert_to_timezone(datetime(2021, 2, 28), "UTC"), 1, convert_to_timezone(datetime(2021, 3, 1), "UTC")),
    # Adding days over a leap day (leap year)
    (convert_to_timezone(datetime(2024, 2, 28), "UTC"), 1, convert_to_timezone(datetime(2024, 2, 29), "UTC")),
])
def test_leap_years(dt, days, expected_dt):
    assert dt + timedelta(days=days) == expected_dt

#
# @pytest.mark.parametrize("dt, hours, timezone_str, expected_dt", [
#     # Subtracting hours across DST start (spring forward)
#     (convert_to_timezone(datetime(2022, 3, 13, 10), "US/Eastern"), -8, "US/Eastern", convert_to_timezone(datetime(2022, 3, 13, 1), "US/Eastern")),
#     # Adding hours across DST end (fall back)
#     (convert_to_timezone(datetime(2022, 11, 6, 1), "US/Eastern"), 2, "US/Eastern", convert_to_timezone(datetime(2022, 11, 6, 1), "US/Eastern")),
# ])
# def test_datetime_arithmetic_across_dst(dt, hours, timezone_str, expected_dt):
#     assert dt + timedelta(hours=hours) == expected_dt

@pytest.mark.parametrize("dt, new_timezone_str, expected_dt", [
    # Convert time from UTC to Asia/Tokyo
    (convert_to_timezone(datetime(2022, 1, 1, 0), "UTC"), "Asia/Tokyo", convert_to_timezone(datetime(2022, 1, 1, 9), "Asia/Tokyo")),
    # Convert time from Asia/Tokyo to Europe/London
    (convert_to_timezone(datetime(2022, 1, 1, 0), "Asia/Tokyo"), "Europe/London", convert_to_timezone(datetime(2021, 12, 31, 15), "Europe/London")),
])
def test_timezone_conversion(dt, new_timezone_str, expected_dt):
    assert dt.astimezone(make_timezone_obj(new_timezone_str)) == expected_dt