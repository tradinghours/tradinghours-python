from tradinghours.market import Market, MarketHoliday
from tradinghours.currency import Currency

print("\nMarkets")

def test_list_all():
    for market in Market.list_all()[:3]:
        print(market)

test_list_all()


def test_get_by_finid_or_mic():
    # Get by either FinID or MIC
    market = Market.get('US.NYSE')
    print(market)
    market = Market.get('XNYS')
    print(market)

print("Get by finid or mic")
test_get_by_finid_or_mic()


def test_follow_market():
    # AR.BCBA is permanently closed and replaced by AR.BYMA
    market = Market.get('AR.BCBA')
    original = Market.get('AR.BCBA', follow=False)

    print(market.fin_id)  # AR.BYMA
    print(original.fin_id)  # AR.BCBA

print("\nFollow Markets")
test_follow_market()

def test_holidays_list_range():
    holidays = MarketHoliday.list_range('US.NYSE', "2024-01-01", "2024-12-31")
    for holiday in holidays[:3]:
        print(holiday)

print("\nHolidays")
test_holidays_list_range()

def test_generate_schedules():
    market = Market.get('XNYS')
    for concrete_phase in market.generate_schedules("2023-09-01", "2023-09-30")[:3]:
        print(concrete_phase)

print("\nSchedules")
test_generate_schedules()


def test_currency_list_holidays():
    currency = Currency.get('AUD')
    for holiday in currency.list_holidays("2023-06-01", "2023-12-31")[:3]:
        print(holiday)

# print("\nCurrency")
# test_currency_list_holidays()
