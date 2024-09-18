import os
import pytest
from tradinghours.store import db

@pytest.fixture
def covered_record():
    table = db.table("covered_markets")
    result = db.execute(table.insert().values(fin_id='XX.TEST'))

    # Retrieve the inserted record
    select_stmt = table.select().where(table.c.id == result.inserted_primary_key[0])
    record = db.execute(select_stmt).fetchone()

    yield record

    delete_stmt = table.delete().where(table.c.id == result.inserted_primary_key[0])
    db.execute(delete_stmt)



