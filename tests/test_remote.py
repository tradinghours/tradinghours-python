import pytest
import csv

from tradinghours.catalog import default_catalog, default_data_manager, MarketFile
from tradinghours.models.market import Market


def test_no_duplicates():

    collection = default_catalog.find_model_collection(Market)
    cluster = collection.clusters.get("us")

    market_file = MarketFile(default_data_manager.csv_dir)
    market_file.ingest(default_catalog.store)
    cluster.flush()

    market_file.ingest(default_catalog.store)
    cluster.flush()

    keys = set()
    with open(cluster.location, "r", encoding="utf-8", newline="") as file:
        for row in csv.reader(file):
            if row[0] in keys:
                pytest.fail("Data was duplicated")
            keys.add(row[0])







