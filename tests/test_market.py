import pytest, calendar
from tradinghours import Market
from tradinghours.dynamic_models import MarketHoliday
from tradinghours.exceptions import DateNotAvailable
import tradinghours.store as st
from .utils import fromiso

# Test whether you can follow or not a permanently closed market
@pytest.mark.parametrize("method, args, expected", [
    (Market.get, ("XBUE",), "AR.BYMA"),
    (Market.get, ("XBUE", False), "AR.BCBA"),
    (Market.get, ("AR.BCBA",), "AR.BYMA"),
    (Market.get, ("AR.BCBA", False), "AR.BCBA"),
    (Market.get_by_mic, ("XBUE",), "AR.BYMA"),
    (Market.get_by_mic, ("XBUE", False), "AR.BCBA"),
    (Market.get_by_finid, ("AR.BCBA",), "AR.BYMA"),
    (Market.get_by_finid, ("AR.BCBA", False), "AR.BCBA"),
])
def test_market_follow(method, args, expected):

    market = method(*args)
    result = str(market.fin_id)
    assert result == expected

# Test whether MIC case is ignored
@pytest.mark.parametrize("method, identifier, expected", [
    (Market.get_by_finid, "AR.BYMA", "AR.BYMA"),
    (Market.get_by_finid, "ar.byma", "AR.BYMA"),
    (Market.get_by_finid, "aR.ByMa", "AR.BYMA"),
    (Market.get_by_mic, "XBUE", "AR.BYMA"),
    (Market.get_by_mic, "xbue", "AR.BYMA"),
    (Market.get_by_mic, "xBuE", "AR.BYMA"),
])
def test_market_case_insensitivity(method, identifier, expected):
    market = method(identifier)
    result = str(market.fin_id)
    assert result == expected


def test_market_list_all():
    found = Market.list_all()
    assert len(found) == len(list(st.db.query(Market.table)))

    found = Market.list_all("US*")
    assert all(f.fin_id.startswith("US") for f in found)

@pytest.mark.parametrize("fin_id", [
    "US.NYSE", "US.CME.EQUITY.USINDEX1", "US.CBOE.VIX"
])
def test_market_available_dates(fin_id):
    market = Market.get(fin_id)
    table = MarketHoliday.table

    first_should_be = st.db.query(table).filter(
            table.c.fin_id == fin_id
        ).order_by(
            table.c.date
        ).first().date.replace(day=1)

    last_should_be = st.db.query(table).filter(
            table.c.fin_id == fin_id
        ).order_by(
            table.c.date.desc()
        ).first().date
    _, num_days_in_month = calendar.monthrange(last_should_be.year, last_should_be.month)
    last_should_be = last_should_be.replace(day=num_days_in_month)

    assert market.first_available_date == first_should_be
    assert market.last_available_date == last_should_be

    if st.db.access_level != st.AccessLevel.only_holidays:
        with pytest.raises(DateNotAvailable):
            list(market.generate_phases("1900-01-01", "2020-01-01"))
        with pytest.raises(DateNotAvailable):
            list(market.generate_phases("2020-01-01", "2099-01-01"))
        with pytest.raises(DateNotAvailable):
            list(market.generate_phases("1900-01-01", "2099-01-01"))

"""
{
         "status":"Open",
         "reason":"Market Holiday - Primary Trading Session (Partial)",
         "until":"2020-11-27T12:45:00-05:00",
         "next_bell":"2020-11-27T13:00:00-05:00",
         "timezone":"America/New_York",
      }
"""

@pytest.mark.parametrize("fin_id, datetime, expected", [
    ("US.NYSE", fromiso("2023-11-15 12:00", "America/New_York"),
     {
         "status": "Open",
         "reason": "Primary Trading Session",
         "until": fromiso("2023-11-15 15:50", "America/New_York"),
         "next_bell": fromiso("2023-11-15 16:00", "America/New_York"),
         "timezone": "America/New_York",
     }),
    ("US.NYSE", fromiso("2023-11-15 18:00", "America/New_York"),
     {
         "status": "Closed",
         "reason": "Post-Trading Session",
         "until": fromiso("2023-11-15 20:00", "America/New_York"),
         "next_bell": fromiso("2023-11-16 09:30", "America/New_York"),
         "timezone": "America/New_York",
     }),
    ("US.NYSE", fromiso("2023-11-11 18:00", "America/New_York"),
     {
         "status": "Closed",
         "reason": None,
         "until": fromiso("2023-11-13 04:00", "America/New_York"),
         "next_bell": fromiso("2023-11-13 09:30", "America/New_York"),
         "timezone": "America/New_York",
     }),
    ("US.NYSE", fromiso("2023-11-24 10:00", "America/New_York"),
     {
         "status": "Open",
         "reason": "Thanksgiving Day - Primary Trading Session (Partial)",
         "until": fromiso("2023-11-24 13:00", "America/New_York"),
         "next_bell": fromiso("2023-11-24 13:00", "America/New_York"),
         "timezone": "America/New_York",
     }),
    ("US.NYSE", fromiso("2024-12-25 10:00", "America/New_York"),
     {
         "status": "Closed",
         "reason": "Christmas",
         "until": fromiso("2024-12-26 04:00", "America/New_York"),
         "next_bell": fromiso("2024-12-26 09:30", "America/New_York"),
         "timezone": "America/New_York",
     })
])
def test_market_status(fin_id, datetime, expected):
    market = Market.get(fin_id)
    status = market.status(datetime=datetime)
    assert status == expected




