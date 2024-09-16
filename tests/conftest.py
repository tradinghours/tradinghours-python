import os
import pytest
from tradinghours.store import db

@pytest.fixture
def level():
    """
    values for API_KEY_LEVEL:
        full = access to all data
        no_currencies = full except for currencies
        only_holidays = only holidays
    """
    return db.access_level

