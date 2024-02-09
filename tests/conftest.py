import os
import pytest

@pytest.fixture
def level():
    """
    values for API_KEY_LEVEL:
        full = access to all data
        no_currencies = full except for currencies
        only_holidays = only holidays
    """

    return os.environ.get("API_KEY_LEVEL", "full").strip()

