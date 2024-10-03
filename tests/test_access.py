import pytest
from tradinghours import store as st
from tradinghours import exceptions as ex
from tradinghours import Currency, Market


# test that the access_level in db is set correctly
def test_access_level():
    tables = st.db.metadata.tables

    if st.tname("schedules") not in tables:
        should_be = st.AccessLevel.only_holidays
    elif st.tname("currencies") not in tables:
        should_be = st.AccessLevel.no_currencies
    else:
        should_be = st.AccessLevel.full

    assert st.db.access_level == should_be


def test_raises_no_access():
    """
    The level doesn't need to be changed in this test.
     Github Actions will run the test suite with data loaded using
     API keys of different access levels.
    """
    # These should never raise NoAccess
    Market.list_all()
    nyse = Market.get("US.NYSE")
    nyse.list_holidays("2024-01-01", "2025-01-01")
    if st.db.access_level == st.AccessLevel.full:
        nyse.list_schedules()
        list(nyse.generate_phases("2024-09-12", "2024-09-13"))
        return

    # these should raise NoAccess for any level != full
    with pytest.raises(ex.NoAccess):
        Currency.get("EUR")
    with pytest.raises(ex.NoAccess):
        Currency.list_all()

    if st.db.access_level == st.AccessLevel.no_currencies:
        # these should work with full and no_currencies
        nyse.list_schedules()
        list(nyse.generate_phases("2024-09-12", "2024-09-13"))

    elif st.db.access_level == st.AccessLevel.only_holidays:
        with pytest.raises(ex.NoAccess):
            nyse.list_schedules()
        with pytest.raises(ex.NoAccess):
            list(nyse.generate_phases("2024-09-12", "2024-09-13"))


def test_raise_not_covered(covered_market, covered_currency):
    """
    NotCovered should be raised when
     Market.get(fin_id)
        not in csvs and not in covered

     (it should raise NoAccess when
       Market.get(fin_id) not in csvs but in covered)

    I need to add a test value

     Currency.get(code) should raise NotCovered when it is not found
    """
    with pytest.raises(ex.NotCovered):
        Market.get("XX.NOTCOVERED")
    assert Market.is_available("XX.NOTCOVERED") is False
    assert Market.is_covered("XX.NOTCOVERED") is False

    with pytest.raises(ex.NoAccess):
        Market.get(covered_market.fin_id)
    assert Market.is_available(covered_market.fin_id) is False
    assert Market.is_covered(covered_market.fin_id) is True

    # should raise nothing
    Market.get("US.NYSE")
    assert Market.is_available("US.NYSE") is True
    assert Market.is_covered("US.NYSE") is True

    if st.db.access_level == st.AccessLevel.full:
        with pytest.raises(ex.NotCovered):
            Currency.get("NOTCOVERED")
        assert Currency.is_available("NOTCOVERED") is False
        assert Currency.is_covered("NOTCOVERED") is False

        # should raise NoAccess with the covered_currency,
        # which is not available under the current plan
        with pytest.raises(ex.NoAccess):
            Currency.get(covered_currency.currency_code)
        assert Currency.is_available(covered_currency.currency_code) is False
        assert Currency.is_covered(covered_currency.currency_code) is True

        # should raise nothing
        Currency.get("EUR")
        assert Currency.is_available("EUR") is True
        assert Currency.is_covered("EUR") is True

    else:
        with pytest.raises(ex.NoAccess):
            Currency.get("NOTCOVERED")

        with pytest.raises(ex.NoAccess):
            assert Currency.is_covered(covered_currency.currency_code) is True
        assert Currency.is_available("NOTCOVERED") is False

        with pytest.raises(ex.NoAccess):
            Currency.get("EUR")
        assert Currency.is_available("EUR") is False

        with pytest.raises(ex.NoAccess):
            Currency.is_covered("EUR")









