from pathlib import Path
from typing import Dict, Generator, Optional, Self, Type, TypeVar

from .base import BaseObject
from .currency import Currency, CurrencyHoliday
from .market import Market, MarketHoliday
from .schedule import Schedule
from .store import Collection, SourceFile, Store
from .typing import StrOrPath

B = TypeVar("B", bound=BaseObject)


class DeclaredFile(SourceFile[B]):
    """Well known source file"""

    known_files: Dict[str, Type["DeclaredFile"]] = {}

    name: str = None
    model: Type[B] = None

    def __init__(self, root: StrOrPath):
        super().__init__(root, self.name, self.model)

    def __init_subclass__(cls):
        super().__init_subclass__()
        if cls.name is None:
            raise ValueError("name must be defined")
        if cls.model is None:
            raise ValueError("model must be defined")
        cls.known_files[cls.name] = cls

    def pre_ingest(self, store: "Store"):
        pass

    def resolve_cluster(self, item: Type[B]) -> Optional[str]:
        return None

    def resolve_key(self, item: Type[B]) -> Optional[str]:
        return None

    def ingest(self, store: "Store"):
        self.pre_ingest(store)
        for current in self.load_iter():
            collection = self.name
            cluster = self.resolve_cluster(current)
            key = self.resolve_key(current)
            data = current.to_tuple()
            store.store_tuple(data, collection, cluster=cluster, key=key)


class CurrencyFile(DeclaredFile[Currency]):
    name = "currencies"
    model = Currency

    def resolve_key(self, item: Currency) -> Optional[str]:
        return item.code


class CurrencyHolidayFile(DeclaredFile[CurrencyHoliday]):
    name = "currency_holidays"
    model = CurrencyHoliday

    def resolve_cluster(self, item: CurrencyHoliday) -> Optional[str]:
        return item.currency_code

    def resolve_key(self, item: CurrencyHoliday) -> Optional[str]:
        return item.date


class MarketFile(DeclaredFile[Market]):
    name = "markets"
    model = Market

    def resolve_cluster(self, item: MarketHoliday) -> Optional[str]:
        return item.fin_id.country

    def resolve_key(self, item: MarketHoliday) -> Optional[str]:
        return str(item.fin_id)


class MarketHolidayFile(DeclaredFile[MarketHoliday]):
    name = "holidays"
    model = MarketHoliday

    def resolve_cluster(self, item: MarketHoliday) -> Optional[str]:
        return str(item.fin_id)

    def resolve_key(self, item: MarketHoliday) -> Optional[str]:
        return item.date


class ScheduleFile(DeclaredFile[Schedule]):
    name = "schedules"
    model = Schedule

    def resolve_cluster(self, item: MarketHoliday) -> Optional[str]:
        return str(item.fin_id)

    def pre_ingest(self, store: "Store"):
        store.clear_collection(self.name)


class Catalog:
    """Gives you access to an underlying data store

    TODO: maybe DeclaredFile and Store.ingest all should be here

    """

    def __init__(self, store: Store):
        self._store = store

    @property
    def store(self) -> Store:
        return self._store

    def ingest_all(self, data_folder: Path):
        for _, declared_class in DeclaredFile.known_files.items():
            source = declared_class(data_folder)
            source.ingest(self.store)

    def find_model_collection(self, model: Type[BaseObject]) -> Collection:
        for name, declared in DeclaredFile.known_files.items():
            if declared.model is model:
                return self.store.collections.get(name)

    def list_all(self, model: Type[B]) -> Generator[B, None, None]:
        collection = self.find_model_collection(model)
        for cluster in collection.clusters:
            cluster_data = cluster.load_all()
            for _, current in cluster_data.items():
                yield model.from_tuple(current)

    def get(
        self, model: Type[BaseObject], key: str, cluster: Optional[str] = None
    ) -> Optional[BaseObject]:
        collection = self.find_model_collection(model)
        cluster_name = cluster or "default"
        cluster = collection.clusters.get(cluster_name)
        cluster_data = cluster.load_all()
        for current_key, data in cluster_data.items():
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
        cluster_data = cluster.load_all()
        for current_key, data in cluster_data.items():
            if current_key >= key_start and current_key <= key_end:
                yield model.from_tuple(data)
        return None

    @classmethod
    def load_default(cls) -> Self:
        data_folder = Path(__file__).parent.parent.parent / "data"
        store = Store(data_folder / "store")
        store.touch()
        return cls(store)


default_catalog = Catalog.load_default()


if __name__ == "__main__":
    from tradinghours.market import Market

    print("Importing...")
    data_folder = Path(__file__).parent.parent.parent / "data"
    default_catalog.ingest_all(data_folder)

    print("Loading...")
    loaded = list(default_catalog.list_all(Market))

    print("Done", len(loaded))
