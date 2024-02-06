from tradinghours.market import Market, MarketHoliday
from tradinghours.currency import Currency, CurrencyHoliday
from tradinghours.schedule import ConcretePhase

from pprint import pprint
# print("\nMarkets")

def test_market_list_all():

    for obj in Market.list_all():
        assert str(obj) == Market.get_string_format().format(**obj.data)


def test_get_by_finid_or_mic():
    # Get by either FinID or MIC
    market = Market.get('US.NYSE')
    assert str(market) == "Market: US.NYSE New York Stock Exchange America/New_York"
    market = Market.get('XNYS')
    assert str(market) == "Market: US.NYSE New York Stock Exchange America/New_York"


def test_follow_market():
    # AR.BCBA is permanently closed and replaced by AR.BYMA
    market = Market.get('AR.BCBA')
    original = Market.get('AR.BCBA', follow=False)

    assert market.fin_id == "AR.BYMA"
    assert original.fin_id == "AR.BCBA"


def test_market_list_holidays():
    holidays = Market.get('US.NYSE').list_holidays("2024-01-01", "2024-12-31")

    for obj in holidays[:3]:
        assert str(obj) == MarketHoliday.get_string_format().format(**obj.data)



def test_generate_schedules():
    market = Market.get('XNYS')
    schedules = market.generate_schedules("2023-09-01", "2023-09-30")

    for obj in schedules:
        assert str(obj) == ConcretePhase.get_string_format().format(**obj.data)



def test_currencies_list_all():
    for obj in Currency.list_all():
        assert str(obj) == Currency.get_string_format().format(**obj.data)



def test_currency_list_holidays():
    currency = Currency.get('AUD')

    for obj in currency.list_holidays("2023-06-01", "2023-12-31"):
        assert str(obj) == CurrencyHoliday.get_string_format().format(**obj.data)



if __name__ == '__main__':
    nprint = lambda *s: print("\n", *s)

    print("Markets:")
    test_market_list_all()
    nprint("Markets:")
    test_get_by_finid_or_mic()
    nprint("Market.fin_ids:")
    test_follow_market()
    nprint("MarketHolidays:")
    test_market_list_holidays()
    nprint("Schedules:")
    test_generate_schedules()
    nprint("Currency:")
    test_currencies_list_all()
    nprint("CurrencyHolidays:")
    test_currency_list_holidays()