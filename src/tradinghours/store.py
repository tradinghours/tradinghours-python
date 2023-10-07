import csv
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generator, Generic, Iterator, Optional, Tuple, Type, TypeVar

from .base import BaseObject
from .typing import StrOrPath
from .util import slugify

B = TypeVar("B", bound=BaseObject)
T = TypeVar("T")


class SourceFile(Generic[B]):
    """Represents a file to be imported"""

    def __init__(self, root: StrOrPath, name: str, model: Type[B]):
        if name is None:
            raise ValueError("name is missing")
        if isinstance(name, str):
            self._name = name
        else:
            raise TypeError("name must be str")

        if root is None:
            raise ValueError("root is missing")
        if isinstance(root, str):
            self._root = Path(root)
        elif isinstance(root, Path):
            self._root = root
        else:
            raise TypeError("root must be str or Path")

        if model is None:
            raise ValueError("model is missing")
        if issubclass(model, BaseObject):
            self._model: BaseObject = model
        else:
            raise TypeError("model must be a BaseObject")

    @property
    def name(self) -> str:
        return self._name.replace("-", "_")

    @property
    def root(self) -> Path:
        return self._root

    @property
    def model(self) -> Type[B]:
        return self._model

    @property
    def filename(self) -> str:
        return self._name.replace("_", "-") + ".csv"

    @property
    def path(self) -> Path:
        return self._root / self.filename

    def load_iter(self) -> Generator[B, None, None]:
        with open(self.path, "r", encoding="utf-8-sig", errors="replace") as file:
            for row in csv.DictReader(file):
                yield self.model.from_dict(row)


class Registry(ABC, Generic[T]):
    """Keeps track of keyed resources"""

    def __init__(self):
        self._resources = {}
        for name in self.discover():
            self.get(name)

    def get(self, name: str) -> T:
        slug = slugify(name)
        resource = self._resources.get(slug, None)
        if resource is None:
            resource = self.create(slug)
            self._resources[slug] = resource
        return resource

    @abstractmethod
    def create(self, slug: str) -> T:
        raise NotImplementedError()

    def discover(self):
        pass

    def __iter__(self) -> Iterator[T]:
        return iter(self._resources.values())


class Cluster:
    """Manages one page file with items for a collection"""

    def __init__(self, location: Path):
        self._location = location
        self._file = open(self.location, "a+", encoding="utf-8", newline="")
        self._writer = csv.writer(self._file)

    @property
    def location(self) -> Path:
        return self._location

    def close(self):
        self._file.close()

    def truncate(self):
        self._file.seek(0)
        self._file.truncate(0)

    def append(self, key: Optional[str], data: Tuple):
        record = [key, *data]
        self._writer.writerow(record)

    def items(self) -> Generator[Tuple[str, Tuple], None, None]:
        # TODO: seek EOF after start iterating
        self._file.seek(0)
        reader = csv.reader(self._file)
        for row in reader:
            key = row[0]
            data = row[1:]
            yield key, data


class ClusterRegistry(Registry[Cluster]):
    """Holds a series of clusters"""

    def __init__(self, folder: Path):
        self._folder = folder
        super().__init__()

    @property
    def folder(self) -> Path:
        return self._folder

    def create(self, slug: str) -> Cluster:
        location = self.folder / f"{slug}.dat"
        return Cluster(location)

    def discover(self) -> Generator[str, None, None]:
        for item in self.folder.iterdir():
            if item.is_file():
                yield item.name


class Collection:
    """Manages a collection of items in a store"""

    def __init__(self, folder: Path):
        self._folder = folder
        self._clusters = ClusterRegistry(folder)

    @property
    def folder(self) -> Path:
        return self._folder

    @property
    def clusters(self) -> ClusterRegistry:
        return self._clusters

    def touch(self):
        self.folder.mkdir(exist_ok=True)

    def clear(self):
        for current in self._clusters:
            current.truncate()
        self._clusters = ClusterRegistry(self.folder)


class CollectionRegistry(Registry[Collection]):
    """Holds a series of collections"""

    def __init__(self, root: Path):
        self._root = root
        super().__init__()

    @property
    def root(self) -> Path:
        return self._root

    def create(self, slug: str) -> Collection:
        folder = self.root / slug
        collection = Collection(folder)
        collection.touch()
        return collection

    def discover(self) -> Generator[str, None, None]:
        for item in self.root.iterdir():
            if item.is_dir():
                yield item.name


class Store:
    """Manages data loaded into memory"""

    def __init__(self, root: Path):
        self._root = root
        self._collections = CollectionRegistry(self._root)

    @property
    def root(self) -> Path:
        return self._root

    @property
    def collections(self) -> CollectionRegistry:
        return self._collections

    def touch(self):
        self.root.mkdir(exist_ok=True)

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
            cluster = "unique"
        cluster_obj = collection_obj.clusters.get(cluster)
        cluster_obj.append(key, data)

    def close(self):
        for current_collection in self.collections:
            for current_cluster in current_collection.clusters:
                current_cluster.close()


if __name__ == "__main__":
    import time

    from .market import Market

    start = time.time()
    data_folder = Path(__file__).parent.parent.parent / "data"
    store = Store(data_folder / "store")
    store.touch()
    store.ingest_all(data_folder)
    elapsed = time.time() - start
    print("Elapsed time", elapsed)

    start = time.time()
    collection = store.collections.get("markets")
    cluster = collection.clusters.get("qa")
    for key, current in cluster.items():
        market = Market.from_tuple(current)
        print(key, market)
    elapsed = time.time() - start

    store.close()

    print("Elapsed time", elapsed)
