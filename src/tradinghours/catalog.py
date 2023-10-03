from pathlib import Path
from typing import Generator, Optional, Self, Type

from .base import BaseObject
from .store import Collection, DeclaredFile, Store


class Catalog:
    """Gives you access to an underlying data store

    TODO: maybe DeclaredFile and Store.ingest all should be here

    """

    def __init__(self, store: Store):
        self._store = store

    @property
    def store(self) -> Store:
        return self._store

    def find_model_collection(self, model: Type[BaseObject]) -> Collection:
        for name, declared in DeclaredFile.known_files.items():
            if declared.model is model:
                return self.store.collections.get(name)

    def list_all(self, model: Type[BaseObject]) -> Generator[BaseObject, None, None]:
        collection = self.find_model_collection(model)
        for cluster in collection.clusters:
            for _, current in cluster.items():
                yield model.from_tuple(current)

    def get(
        self, model: Type[BaseObject], key: str, cluster: Optional[str] = None
    ) -> Optional[BaseObject]:
        collection = self.find_model_collection(model)
        cluster_name = cluster or "default"
        cluster = collection.clusters.get(cluster_name)
        for current_key, data in cluster.items():
            if current_key == key:
                return model.from_tuple(data)
        return None

    def filter(
        self,
        model: Type[BaseObject],
        key_start: str,
        key_end: str,
        cluster: Optional[str] = None,
    ) -> Generator[BaseObject, None, None]:
        collection = self.find_model_collection(model)
        cluster_name = cluster or "default"
        cluster = collection.clusters.get(cluster_name)
        for current_key, data in cluster.items():
            if current_key >= key_start and current_key <= key_end:
                yield model.from_tuple(data)
        return None

    @classmethod
    def load_default(cls) -> Self:
        # TODO: need to know all clusters on load
        data_folder = Path(__file__).parent.parent.parent / "data"
        store = Store(data_folder / "store")
        return cls(store)


default_catalog = Catalog()
