from typing import Dict, Generator, Optional, Tuple, Type, TypeVar

from .validate import validate_str_arg

from .base import BaseObject
from .models.market import Market, MarketHoliday, MicMapping
from .models.season import SeasonDefinition
from .models.currency import CurrencyHoliday, Currency
from .models.schedule import Schedule, PhaseType
from .remote import default_data_manager
from .store.engine import Store, default_store
from .store.file import FileCollection
from .store.source import SourceFile
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
            key = str(key).upper() if key else key

            data = current._to_tuple(raw=True)
            store.store_tuple(data, collection, cluster=cluster, key=key)


class SeasonDefinitionFile(DeclaredFile):
    name = "season-definitions"
    model = SeasonDefinition


class CurrencyFile(DeclaredFile[Currency]):
    name = "currencies"
    model = Currency

    def resolve_key(self, item: Currency) -> Optional[str]:
        return item.currency_code


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
        return item.fin_id_obj.country

    def resolve_key(self, item: MarketHoliday) -> Optional[str]:
        return str(item.fin_id)


class MarketHolidayFile(DeclaredFile[MarketHoliday]):
    name = "holidays"
    model = MarketHoliday

    def resolve_cluster(self, item: MarketHoliday) -> Optional[str]:
        return str(item.fin_id)

    def resolve_key(self, item: MarketHoliday) -> Optional[str]:
        return item.date


class MicMappingFile(DeclaredFile[MicMapping]):
    name = "mic-mapping"
    model = MicMapping

    def resolve_key(self, item: MicMapping) -> Optional[str]:
        return item.mic

class ScheduleFile(DeclaredFile[Schedule]):
    name = "schedules"
    model = Schedule

    def resolve_cluster(self, item: MarketHoliday) -> Optional[str]:
        return str(item.fin_id)

    def pre_ingest(self, store: "Store"):
        store.clear_collection(self.name)

class PhaseTypeFile(DeclaredFile[PhaseType]):
    name = "phases"
    model = PhaseType



class Catalog:
    """Gives you access to an underlying data store

    TODO: maybe DeclaredFile and Store.ingest all should be here

    """

    def __init__(self, store: Store):
        self._store = store

    @property
    def store(self) -> Store:
        return self._store

    def ingest_all(self):
        for _, declared_class in DeclaredFile.known_files.items():
            source = declared_class(default_data_manager.csv_dir)
            source.ingest(self.store)
        self.store.flush()

    def find_model_collection(self, model: Type[BaseObject]) -> FileCollection:
        for name, declared in DeclaredFile.known_files.items():
            if declared.model is model:
                return self.store.collections.get(name)
        return None

    def list_all(self, model: Type[B]) -> Generator[B, None, None]:
        collection = self.find_model_collection(model)
        for cluster in collection.clusters:
            cluster_data = cluster.load_all()
            for _, current in cluster_data.items():
                yield model.from_tuple(current)

    def list(
        self, model: Type[B], cluster: Optional[str] = None
    ) -> Generator[Tuple[str, B], None, None]:
        collection = self.find_model_collection(model)
        cluster_name = cluster or "default"
        cluster_obj = collection.clusters.get(cluster_name)
        cluster_data = cluster_obj.load_all()
        for current_key, data in cluster_data.items():
            yield current_key, model.from_tuple(data)
        return None

    def get(
        self, model: Type[B], key: str, cluster: Optional[str] = None
    ) -> Optional[B]:
        key = validate_str_arg("key", key).upper()
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
        model: Type[B],
        key_start: str,
        key_end: str,
        cluster: Optional[str] = None,
    ) -> Generator[B, None, None]:
        key_start = validate_str_arg("key_start", key_start).upper()
        key_end = validate_str_arg("key_end", key_end).upper()
        collection = self.find_model_collection(model)
        cluster_name = cluster or "default"
        cluster = collection.clusters.get(cluster_name)
        cluster_data = cluster.load_all()
        for current_key, data in cluster_data.items():
            if current_key >= key_start and current_key <= key_end:
                yield model.from_tuple(data)
        return None


default_catalog = Catalog(default_store)


if __name__ == "__main__":
    from datetime import date
    from time import time

    print("\nDownloading...")
    start = time()
    default_data_manager.download()
    elapsed = time() - start
    print("Elapsed seconds", elapsed)

    print("\nImporting...")
    start = time()
    default_catalog.ingest_all()
    elapsed = time() - start
    print("Elapsed seconds", elapsed)

    print("\nLoading Market...")
    start = time()
    us_market: Market = default_catalog.get(Market, "US.IEX", "us")
    elapsed = time() - start
    print("Elapsed seconds", elapsed)

    print("\nListing Holidays...")
    start = time()
    loaded = list(us_market.list_holidays("2023-06-01", "2023-12-31"))
    elapsed = time() - start
    print("Elapsed seconds", elapsed, len(loaded))

    print("\nListing Currencies...")
    start = time()
    loaded = list(Currency.list_all())
    elapsed = time() - start
    print("Elapsed seconds", elapsed, len(loaded))

    print("\nListing Schedules...")
    start = time()
    loaded = list(Schedule.list_all())
    elapsed = time() - start
    print("Elapsed seconds", elapsed, len(loaded))

    print("\nGenerating Schedules...")
    start = time()
    for concrete in us_market.generate_phases(date(2023, 9, 1), date(2023, 9, 30)):
        print(concrete)
    elapsed = time() - start
    print("Elapsed seconds", elapsed, len(loaded))

    print("\nDone")
