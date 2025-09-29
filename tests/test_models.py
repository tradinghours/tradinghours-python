import os
import pytest

from tradinghours.market import Market, MarketHoliday
from tradinghours.currency import Currency
from tradinghours.models import PhaseType, SeasonDefinition
from tradinghours.exceptions import NoAccess
import tradinghours.store as st

def test_market_instance_fields():
    nyse = Market.get("US.NYSE")
    assert nyse.fin_id == "US.NYSE"
    # assert nyse.fin_id_obj.country == "US"
    # assert nyse.fin_id_obj.acronym == "NYSE"
    # assert str(nyse.fin_id_obj) == "US.NYSE"

    assert nyse.mic == "XNYS"
    assert nyse.weekend_definition == "Sat-Sun"
    # assert str(nyse.weekend_definition_obj) == "Sat-Sun"

def test_market_holiday_instance_fields():
    nyse = Market.get("XNYS")
    holidays = nyse.list_holidays("2007-11-20", "2007-11-23")
    assert len(holidays) == 2

    first, second = holidays
    assert first.holiday_name == "Thanksgiving Day"
    assert first.settlement == 'No'
    assert first.has_settlement is False
    assert first.status == 'Closed'
    assert first.is_open is False
    assert first.observed is False

    assert second.holiday_name == "Thanksgiving Day"
    assert second.settlement == 'Yes'
    assert second.has_settlement is True
    assert second.status == 'Open'
    assert second.is_open is True
    assert second.observed is True


@pytest.mark.xfail(
    st.db.access_level != st.AccessLevel.full,
    reason="No access", strict=True, raises=NoAccess
)
def test_currency_instance_fields():
    aud = Currency.get("AUD")
    assert aud.weekend_definition == "Sat-Sun"


def test_phase_type_instance_fields():
    if st.db.access_level == st.AccessLevel.only_holidays:
        with pytest.raises(NoAccess) as exception:
            PhaseType.as_dict()
        return
    else:
        phase_types = PhaseType.as_dict()

    assert len(phase_types) == 13
    expected = {
        'Primary Trading Session': ('Primary Trading Session', 'Open', 'Yes', True, True),
        'Primary Trading Session, No Settlement': ('Primary Trading Session, No Settlement', 'Open', 'No', False, True),
        'Primary Trading Session, No Closing Price': ('Primary Trading Session, No Closing Price', 'Open', 'No', False, True),
        'Intermission': ('Intermission', 'Closed', 'No', False, False),
        'Pre-Trading Session': ('Pre-Trading Session', 'Closed', 'No', False, False),
        'Post-Trading Session': ('Post-Trading Session', 'Closed', 'No', False, False),
        'Trading-at-Last': ('Trading-at-Last', 'Closed', 'No', False, False),
        'Pre-Open': ('Pre-Open', 'Closed', 'No', False, False),
        'Pre-Close': ('Pre-Close', 'Closed', 'No', False, False),
        'Order Collection Period': ('Order Collection Period', 'Closed', 'No', False, False),
        'Call Auction': ('Call Auction', 'Closed', 'No', False, False),
        'Settlement Window': ('Settlement Window', 'Closed', 'No', False, False),
        'Other': ('Other', 'Closed', 'No', False, False),
    }
    for k, phase in phase_types.items():
        assert expected[k] == (str(phase.name),
                               str(phase.status),
                               str(phase.settlement),
                               phase.has_settlement,
                               phase.is_open)


def test_string_format():
    # TODO: go over the error messages that are supposed to be shown
    market = Market.get('US.NYSE')
    assert str(market) == 'Market: US.NYSE New York Stock Exchange America/New_York'

    market_holiday = market.list_holidays("2007-11-20", "2007-11-23")[0]
    assert str(market_holiday) == 'MarketHoliday: US.NYSE 2007-11-22 Thanksgiving Day'

    if st.db.access_level != st.AccessLevel.full:
        with pytest.raises(NoAccess):
            Currency.get('AUD')
        # assert str(exception.value) == "You didn't run `tradinghours import` or you dont have access to currencies."
    else:
        currency = Currency.get('AUD')
        assert str(currency) == 'Currency: AUD Australian Dollar'

        currency_holiday = currency.list_holidays("2020-01-27", "2020-01-27")[0]
        assert str(currency_holiday) == 'CurrencyHoliday: AUD 2020-01-27 Australia Day'

    if st.db.access_level == st.AccessLevel.only_holidays:
        with pytest.raises(NoAccess) as exception:
            Market.get("US.NYSE").list_schedules()
        # assert str(exception.value) == r"You didn't run `tradinghours import` or you dont have access to schedules/us-nyse."

        with pytest.raises(NoAccess) as exception:
            list(market.generate_phases("2024-02-06", "2024-02-06"))
        # assert str(exception.value) == r"You didn't run `tradinghours import` or you dont have access to phases."

        with pytest.raises(NoAccess) as exception:
            SeasonDefinition.get("First day of March", 2022)
        # assert str(exception.value) == r"You didn't run `tradinghours import` or you dont have access to season-definitions."

    else:
        schedule = Market.get("US.NYSE").list_schedules()
        assert str(schedule[0]) == "Schedule: US.NYSE (Partial) 06:30:00 - 09:30:00    Mon-Fri Pre-Trading Session"

        schedule = Market.get("US.MGEX").list_schedules()
        assert str(schedule[-1]) == "Schedule: US.MGEX (Thanksgiving2023) 16:45:00 - 08:30:00 +2 Wed Pre-Open"

        concrete_phase = list(market.generate_phases("2024-02-06", "2024-02-06"))[0]
        assert str(concrete_phase) == 'Phase: 2024-02-06 04:00:00-05:00 - 2024-02-06 09:30:00-05:00 Pre-Trading Session'

        season = SeasonDefinition.get("First day of March", 2022)
        assert str(season).lower() == 'SeasonDefinition: 2022-03-01 First day of March'.lower()


def test_set_string_format():
    market = Market.get('ZA.JSE.SAFEX')

    # change format
    Market.set_string_format("{acronym} - {asset_type}")
    assert str(market) == "JSE - Derivatives"

    # change format with class prefix
    Market.set_string_format("{acronym} - {asset_type}", prefix_class=True)
    assert str(market) == "Market: JSE - Derivatives"

    Market.reset_string_format()
    assert str(market) == 'Market: ZA.JSE.EQUITIES.DRV Johannesburg Stock Exchange Africa/Johannesburg'

    holiday = Market.get("XNYS").list_holidays("2022-01-17", "2022-01-17")[0]
    assert str(holiday) == "MarketHoliday: US.NYSE 2022-01-17 Birthday of Martin Luther King, Jr"

    holiday.set_string_format("{holiday_name} on {date} is open: {is_open} and has settlement: {has_settlement}")
    assert str(holiday) == "Birthday of Martin Luther King, Jr on 2022-01-17 is open: False and has settlement: False"

    MarketHoliday.reset_string_format()

def test_market_raw_data():

    nyse = Market.get("XNYS")
    holiday = nyse.list_holidays("2007-11-20", "2007-11-23")[0]
    assert holiday.data["settlement"] == "No"
    assert holiday.data["status"] == "Closed"
    assert holiday.data["observed"] is False


@pytest.mark.xfail(
    st.db.access_level != st.AccessLevel.full,
    reason="No access", strict=True, raises=NoAccess
)
def test_currency_raw_data():
    currency = Currency.get('AUD')
    holiday = currency.list_holidays("2020-01-27", "2020-01-27")[0]
    assert holiday.data["settlement"] == "No"
    assert holiday.data["observed"] is True


