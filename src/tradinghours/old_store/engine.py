import os
from typing import Optional, Tuple

from ..config import main_config
from .base import Collection, Registry


class Store:
    """Manages data loaded into memory"""

    def __init__(self, collections_registry: Registry):
        self._collections = collections_registry

    @property
    def collections(self) -> Registry[Collection]:
        return self._collections

    @property
    def token(self):
        return os.getenv("TRADINGHOURS_TOKEN")

    def clear_collection(self, name: str):
        collection_obj = self.collections.get(name)
        collection_obj.clear()

    def store_tuple(
        self,
        data: Tuple,
        collection,
        cluster: Optional[str] = None,
        key: Optional[str] = None,
    ):
        collection_obj = self.collections.get(collection)
        if cluster is None:
            cluster = "default"
        cluster_obj = collection_obj.clusters.get(cluster)
        cluster_obj.append(key, data)

    def flush(self):
        for collection in self.collections:
            for cluster in collection.clusters:
                cluster.flush()


def create_file_store():
    from tradinghours.store.file import FileCollectionRegistry

    root = main_config.get("data", "local_dir")
    registry = FileCollectionRegistry(root)
    store = Store(registry)
    return store


def create_sql_store():
    from tradinghours.store.sql import SqlCollectionRegistry

    db_url = main_config.get("data", "db_url")
    registry = SqlCollectionRegistry(db_url)
    store = Store(registry)
    return store


def create_default_store():
    if main_config.getboolean("data", "use_db"):
        return create_sql_store()
    else:
        return create_file_store()


default_store = create_default_store()
