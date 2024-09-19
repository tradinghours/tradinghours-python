import pytest, io, sys, os

from tradinghours import Market
from tradinghours.currency import Currency, CurrencyHoliday
from tradinghours.dynamic_models import Phase, MarketHoliday
from tradinghours.exceptions import NoAccess
import tradinghours.store as st
from pathlib import Path


def test_market_list_all():

    for obj in Market.list_all():
        assert str(obj) == Market.get_string_format().format(**obj.to_dict())


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
        assert str(obj) == MarketHoliday.get_string_format().format(**obj.to_dict())


@pytest.mark.xfail(
    st.db.access_level == st.AccessLevel.only_holidays,
    reason="No access", strict=True, raises=NoAccess
)
def test_generate_phases():
    market = Market.get('XNYS')
    schedules = market.generate_phases("2023-09-01", "2023-09-30")

    for obj in schedules:
        assert str(obj) == Phase.get_string_format().format(**obj.to_dict())


@pytest.mark.xfail(
    st.db.access_level != st.AccessLevel.full,
    reason="No access", strict=True, raises=NoAccess
)
def test_currencies_list_all():
    for obj in Currency.list_all():
        assert str(obj) == Currency.get_string_format().format(**obj.to_dict())


@pytest.mark.xfail(
    st.db.access_level != st.AccessLevel.full,
    reason="No access", strict=True, raises=NoAccess
)
def test_currency_list_holidays():
    currency = Currency.get('AUD')
    for obj in currency.list_holidays("2023-06-01", "2023-12-31"):
        assert str(obj) == CurrencyHoliday.get_string_format().format(**obj.to_dict())

def strip(line, sub):
    try:
        return line[:line.index(sub)]
    except ValueError:
        return line

@pytest.mark.xfail(
    st.db.access_level != st.AccessLevel.full,
    reason="No access", strict=True, raises=NoAccess
)
def test_code_blocks():
    with open(Path("README.md"), "r", encoding="utf-8") as readme:
        readme = readme.readlines()

    code_blocks = []
    in_block = False # False=Not in block, True=in code part of block, None=in output part of block
    block = ""
    out = ""
    for line in readme:
        if line.startswith("```python"):
            in_block = True
            block = ""
            out = ""
        elif in_block in (True, None):
            if line.startswith("```"):
                code_blocks.append((block, out))
                in_block = False
                continue
            if line.startswith(">>> ") or in_block is None:
                in_block = None
                out += line[4:]
                continue

            block += line + "\n"

    for code_block, output in code_blocks:
        original_stdout = sys.stdout
        sys.stdout = io.StringIO()
        exec(code_block)
        captured_out = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stdout = original_stdout
        # assert captured_out == output



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
    test_generate_phases()
    nprint("Currency:")
    test_currencies_list_all()
    nprint("CurrencyHolidays:")
    test_currency_list_holidays()