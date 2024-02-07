import pytest

from tradinghours.models.market import Market, MarketHoliday, MicMapping
from tradinghours.models.currency import Currency, CurrencyHoliday
from tradinghours.models.schedule import Schedule
from tradinghours.models.season import SeasonDefinition
from tradinghours.util import snake_case

from pprint import pprint

@pytest.mark.parametrize("model, columns", [
    (Market, ["Exchange Name",
                      "Market Name",
                      "Security Group",
                      "Timezone",
                      "Weekend Definition",
                      "FinID",
                      "MIC",
                      "Acronym",
                      "Asset Type",
                      "Memo",
                      "Permanently Closed",
                      "Replaced By"]
     ),
    (Currency, ["Currency Code",
                "Currency Name",
                "Country Code",
                "Central Bank", 
                "Financial Capital",
                "Financial Capital Timezone",
                "Weekend Definition"]
     ),
    (CurrencyHoliday, ["Currency Code",
                       "Date",
                       "Holiday Name",
                       "Settlement",
                       "Observed",
                       "Memo"]
     ),
    (MarketHoliday, ["FinID",
                     "Date",
                     "Holiday Name",
                     "Schedule",
                     "Settlement",
                     "Observed",
                     "Memo",
                     "Status"]
     ),
    (MicMapping, ["MIC",
                 "FinID"]
     ),
    (Schedule, ["FinID",
                "Schedule Group",
                "Schedule Group Memo",
                "Timezone",
                "Phase Type",
                "Phase Name",
                "Phase Memo",
                "Days",
                "Start",
                "End",
                "Offset Days",
                "Duration",
                "Min Start",
                "Max Start",
                "Min End",
                "Max End",
                "In Force Start Date",
                "In Force End Date",
                "Season Start",
                "Season End"]
     ),
    (SeasonDefinition, ["Season",
                        "Year",
                        "Date"]
     )
])
def test_model_fields(model, columns):

    column_snakes = sorted([snake_case(c) for c in columns])
    field_names = sorted(model.fields)
    assert field_names == column_snakes


def test_instance_fields():
    aud = Currency.get("AUD")
    assert aud.weekend_definition == "Sat-Sun"

    nyse = Market.get("US.NYSE")
    assert nyse.fin_id == "US.NYSE"
    assert nyse.fin_id_obj.country == "US"
    assert nyse.fin_id_obj.acronym == "NYSE"
    assert str(nyse.fin_id_obj) == "US.NYSE"

    assert nyse.mic == "XNYS"
    assert nyse.weekend_definition == "Sat-Sun"
    assert str(nyse.weekend_definition_obj) == "Sat-Sun"

    holidays = nyse.list_holidays("2007-11-20", "2007-11-23")
    assert len(holidays) == 2

    first, second = holidays

    assert first.holiday_name == "Thanksgiving Day"
    assert first.settlement is False
    assert first.status is False
    assert first.observed is False

    assert second.holiday_name == "Thanksgiving Day"
    assert second.settlement is True
    assert second.status is True
    assert second.observed is True


def test_string_format():
    market = Market.get('US.NYSE')
    assert str(market) == 'Market: US.NYSE New York Stock Exchange America/New_York'

    market_holiday = market.list_holidays("2007-11-20", "2007-11-23")[0]
    assert str(market_holiday) == 'MarketHoliday: US.NYSE 2007-11-22 Thanksgiving Day'

    currency = Currency.get('AUD')
    assert str(currency) == 'Currency: AUD Australian Dollar'

    currency_holiday = currency.list_holidays("2020-01-27", "2020-01-27")[0]
    assert str(currency_holiday) == 'CurrencyHoliday: AUD 2020-01-27 Australia Day'

    schedule = Schedule.list_all("US.NYSE")
    assert str(schedule[0]) == "Schedule: US.NYSE 04:00:00 - 09:30:00 Mon-Fri Regular"

    concrete_phase = list(market.generate_schedules("2024-02-06", "2024-02-06"))[0]
    assert str(concrete_phase) == 'Phase: 2024-02-06 04:00:00-05:00 - 2024-02-06 09:30:00-05:00 Pre-Trading Session'

    season = SeasonDefinition.get("First day of March", 2022)
    assert str(season) == 'SeasonDefinition: 2022-03-01 First day of March'

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



def test_raw_data():

    nyse = Market.get("XNYS")
    holiday = nyse.list_holidays("2007-11-20", "2007-11-23")[0]
    assert holiday.raw_data["settlement"] == "No"
    assert holiday.raw_data["status"] == "Closed"
    assert holiday.raw_data["observed"] == ""
    assert holiday.data["settlement"] is False
    assert holiday.data["status"] is False
    assert holiday.data["observed"] is False

    currency = Currency.get('AUD')
    holiday = currency.list_holidays("2020-01-27", "2020-01-27")[0]
    assert holiday.raw_data["settlement"] == "No"
    assert holiday.raw_data["observed"] == "OBS"
    assert holiday.data["settlement"] is False
    assert holiday.data["observed"] is True


