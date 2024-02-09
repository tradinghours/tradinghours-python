import pytest, os
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

from tradinghours import Currency, Market
from tradinghours.exceptions import NoAccess

LEVEL = os.environ.get("API_KEY_LEVEL", "full").strip()

def _convert(naive_dt, timezone_str):
    return naive_dt.replace(tzinfo=ZoneInfo(timezone_str))

#
# @pytest.mark.parametrize("naive_dt, timezone_str, expected_dt", [
#     # Test DST start transition (US/Eastern, 2nd Sunday in March)
#     (datetime(2022, 3, 13, 2), "US/Eastern", _convert(datetime(2022, 3, 13, 3), "US/Eastern")),
#     # Test DST end transition (US/Eastern, 1st Sunday in November)
#     (datetime(2022, 11, 6, 1), "US/Eastern", _convert(datetime(2022, 11, 6, 1), "US/Eastern")),
# ])
# def test_dst_transitions(naive_dt, timezone_str, expected_dt):
#     converted = _convert(naive_dt, timezone_str)
#     print(converted, expected_dt, converted == expected_dt)
#     assert converted == expected_dt, str(converted) + "==" + str(expected_dt)

@pytest.mark.parametrize("dt, days, expected_dt", [
    # Adding days over a leap day (non-leap year)
    (_convert(datetime(2021, 2, 28), "UTC"), 1, _convert(datetime(2021, 3, 1), "UTC")),
    # Adding days over a leap day (leap year)
    (_convert(datetime(2024, 2, 28), "UTC"), 1, _convert(datetime(2024, 2, 29), "UTC")),
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
    (_convert(datetime(2022, 1, 1, 0), "UTC"), "Asia/Tokyo", _convert(datetime(2022, 1, 1, 9), "Asia/Tokyo")),
    # Convert time from Asia/Tokyo to Europe/London
    (_convert(datetime(2022, 1, 1, 0), "Asia/Tokyo"), "Europe/London", _convert(datetime(2021, 12, 31, 15), "Europe/London")),
])
def test_timezone_conversion(dt, new_timezone_str, expected_dt):
    assert dt.astimezone(ZoneInfo(new_timezone_str)) == expected_dt


@pytest.mark.xfail(LEVEL != "full", reason="No access", strict=True, raises=NoAccess)
@pytest.mark.parametrize("currency, timezone", [
    ("BRL", "America/Sao_Paulo"),
    ("CAD", "America/Toronto"),
    ("DKK", "Europe/Copenhagen"),
    ("MYR", "Asia/Kuala_Lumpur")
])
def test_currency_timezone(currency, timezone):
    currency = Currency.get(currency)
    assert currency.financial_capital_timezone == timezone
    assert isinstance(currency.financial_capital_timezone_obj, ZoneInfo)
    assert currency.financial_capital_timezone_obj == ZoneInfo(timezone)



@pytest.mark.parametrize("market, timezone", [
    ("AE.ADX", "Asia/Dubai"),
    ("AU.ASX.NIGHT.DERIVATIVES.SPI", "Australia/Sydney"),
    ("BE.EURONEXT.DERIVATIVES.LIS.FUT", "Europe/Brussels"),
    ("BW.BSE", "Africa/Gaborone")
])
def test_market_timezone(market, timezone):
    market = Market.get(market)
    assert market.timezone == timezone
    assert isinstance(market.timezone_obj, ZoneInfo)
    assert market.timezone_obj == ZoneInfo(timezone)



