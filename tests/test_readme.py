from tradinghours.market import Market, MarketHoliday
from tradinghours.currency import Currency

from pprint import pprint
# print("\nMarkets")

def test_market_list_all():

    expected = [
        'Market: AE.ADX Abu Dhabi Securities Exchange Asia/Dubai',
        'Market: AE.DFM Dubai Financial Market Asia/Dubai',
        'Market: AE.DGCX Dubai Gold & Commodities Exchange Asia/Dubai'
    ]

    for obj, exp in zip(Market.list_all()[:3], expected):
        assert str(obj) == exp


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

    expected = [
        "MarketHoliday: US.NYSE 2024-01-01 New Year's Day",
        "MarketHoliday: US.NYSE 2024-01-15 Birthday of Martin Luther King, Jr",
        "MarketHoliday: US.NYSE 2024-02-19 Washington's Birthday"
    ]
    for obj, exp in zip(holidays[:3], expected):
        assert str(obj) == exp


def test_generate_schedules():
    market = Market.get('XNYS')
    schedules = market.generate_schedules("2023-09-01", "2023-09-30")

    expected = [
        'ConcretePhase: 2023-09-01 04:00:00-04:00 - 2023-09-01 09:30:00-04:00 Pre-Trading Session',
        'ConcretePhase: 2023-09-01 06:30:00-04:00 - 2023-09-01 09:30:00-04:00 Pre-Open',
        'ConcretePhase: 2023-09-01 09:30:00-04:00 - 2023-09-01 09:30:00-04:00 Call Auction'
    ]
    for obj, exp in zip(list(schedules)[:3], expected):
        assert str(obj) == exp


def test_currencies_list_all():
    expected = [
        'Currency: AUD Australian Dollar',
        'Currency: BRL Brazilian Real',
        'Currency: CAD Canadian Dollar'
    ]
    for obj, exp in zip(Currency.list_all()[:3], expected):
        assert str(obj) == exp


def test_currency_list_holidays():
    currency = Currency.get('AUD')

    expected = [
        "CurrencyHoliday: AUD 2023-06-12 King's Birthday",
        "CurrencyHoliday: AUD 2023-10-02 Labor Day",
        "CurrencyHoliday: AUD 2023-12-25 Christmas Day"
    ]
    for obj, exp in zip(currency.list_holidays("2023-06-01", "2023-12-31")[:3], expected):
        assert str(obj) == exp


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