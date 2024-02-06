import pytest

from tradinghours.market import Market, MarketHoliday, MicMapping
from tradinghours.currency import Currency, CurrencyHoliday
from tradinghours.schedule import Schedule
from tradinghours.season import SeasonDefinition
from tradinghours.util import snake_case


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



def test_model_fields():

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

    market = Market.get('ZA.JSE.SAFEX')
    assert str(market) == 'Market: ZA.JSE.EQUITIES.DRV Johannesburg Stock Exchange Africa/Johannesburg'

    # change format
    Market.set_string_format("{acronym} - {asset_type}")
    assert str(market) == "JSE - Derivatives"

    # change format with class prefix
    Market.set_string_format("{acronym} - {asset_type}", prefix_class=True)
    assert str(market) == "Market: JSE - Derivatives"

    Market.reset_string_format()
    assert str(market) == 'Market: ZA.JSE.EQUITIES.DRV Johannesburg Stock Exchange Africa/Johannesburg'


    schedule = Schedule.list_all("US.NYSE")
    assert str(schedule[0]) == "Schedule: US.NYSE 04:00:00 - 09:30:00 Mon-Fri Regular"

    season = SeasonDefinition.get("First day of March", 2022)
    assert str(season) == 'SeasonDefinition: 2022-03-01 First day of March'


