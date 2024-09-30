import os
import pytest
from contextlib import contextmanager
from tradinghours.store import db


@contextmanager
def _select_and_delete(result, table):
    # Retrieve the inserted record
    select_stmt = table.select().where(table.c.id == result.inserted_primary_key[0])
    record = db.execute(select_stmt).fetchone()

    yield record

    delete_stmt = table.delete().where(table.c.id == result.inserted_primary_key[0])
    db.execute(delete_stmt)


@pytest.fixture
def covered_market():
    table = db.table("covered_markets")
    result = db.execute(table.insert().values(fin_id='XX.TEST'))
    with _select_and_delete(result, table) as record:
        yield record


@pytest.fixture
def covered_currency():
    table = db.table("covered_currencies")
    result = db.execute(table.insert().values(currency_code='XXX'))

    with _select_and_delete(result, table) as record:
        yield record



