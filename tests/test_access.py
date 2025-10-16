import pytest
from tradinghours import store as st
from tradinghours import exceptions as ex
from tradinghours import Currency, Market


# test that the access_level in db is set correctly
def test_access_level():
    tables = st.db.metadata.tables

    if "schedules" not in tables:
        should_be = st.AccessLevel.only_holidays
    elif "currencies" not in tables:
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


def test_raises_not_available():
    """
    NoAccess should be raised when a method is not available under the current plan.
    NotAvailable should be raised when a currency or market is not available.
    """
    with pytest.raises(ex.NotAvailable):
        Market.get("XX.NOTCOVERED")

    # should raise nothing
    Market.get("US.NYSE")
    assert Market.is_available("US.NYSE") is True

    if st.db.access_level == st.AccessLevel.full:
        with pytest.raises(ex.NotAvailable):
            Currency.get("NOTCOVERED")
        assert Currency.is_available("NOTCOVERED") is False

        # should raise nothing
        Currency.get("EUR")
        assert Currency.is_available("EUR") is True
    else:
        with pytest.raises(ex.NoAccess):
            Currency.get("NOTCOVERED")
        with pytest.raises(ex.NoAccess):
            Currency.is_available("NOTCOVERED")

        with pytest.raises(ex.NoAccess):
            Currency.get("EUR")
        with pytest.raises(ex.NoAccess):
            Currency.is_available("EUR")








