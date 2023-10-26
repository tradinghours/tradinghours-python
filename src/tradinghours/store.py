import csv
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import (
    Dict,
    Generator,
    Generic,
    Iterator,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
)

from .base import BaseObject
from .config import main_config
from .typing import StrOrPath
from .util import slugify
from .validate import validate_path_arg, validate_str_arg, validate_subclass_arg

B = TypeVar("B", bound=BaseObject)
T = TypeVar("T")


class SourceFile(Generic[B]):
    """Represents a file to be imported"""

    def __init__(self, root: StrOrPath, name: str, model: Type[B]):
        self._name = validate_str_arg("name", name)
        self._root = validate_path_arg("root", root)
        self._model = validate_subclass_arg("model", model, BaseObject)

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

    DEFAULT_CACHE_SIZE = 500

    def __init__(self, location: StrOrPath, cache_size: Optional[int] = None):
        self._location = validate_path_arg("location", location)
        self._cached: List[str, Tuple] = []
        self._cache_size = cache_size or self.DEFAULT_CACHE_SIZE

    @property
    def location(self) -> Path:
        return self._location

    def truncate(self):
        with open(self.location, "a+", encoding="utf-8", newline="") as file:
            file.seek(0)
            file.truncate(0)

    def append(self, key: Optional[str], data: Tuple):
        record = [key, *data]
        self._cached.append(record)
        if len(self._cached) >= self._cache_size:
            self.flush()

    def flush(self):
        with open(self.location, "a+", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerows(self._cached)
            self._cached = []

    def load_all(self) -> Dict[str, Tuple]:
        keyed_items = {}
        with open(self.location, "r", encoding="utf-8", newline="") as file:
            for row in csv.reader(file):
                key = row[0]
                data = row[1:]
                keyed_items[key] = data
        return keyed_items


class ClusterRegistry(Registry[Cluster]):
    """Holds a series of clusters"""

    def __init__(self, folder: StrOrPath):
        self._folder = validate_path_arg("folder", folder)
        super().__init__()

    @property
    def folder(self) -> Path:
        return self._folder

    def create(self, slug: str) -> Cluster:
        location = self.folder / f"{slug}.dat"
        return Cluster(location)

    def discover(self) -> Generator[str, None, None]:
        if self.folder.exists():
            for item in self.folder.iterdir():
                if item.is_file():
                    yield item.stem


class Collection:
    """Manages a collection of items in a store"""

    def __init__(self, folder: StrOrPath):
        self._folder = validate_path_arg("folder", folder)
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

    def __init__(self, root: StrOrPath):
        self._root = validate_path_arg("root", root)
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
        if self.root.exists():
            for item in self.root.iterdir():
                if item.is_dir():
                    yield item.name


class Store:
    """Manages data loaded into memory"""

    def __init__(self, root: StrOrPath):
        self._root = validate_path_arg("root", root)
        self.touch()
        self._collections = CollectionRegistry(self._root)

    @property
    def root(self) -> Path:
        return self._root

    @property
    def collections(self) -> CollectionRegistry:
        return self._collections

    @property
    def token(self):
        return os.getenv("TRADINGHOURS_TOKEN")

    def touch(self):
        self.root.mkdir(parents=True, exist_ok=True)

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


default_store = Store(main_config.get("data", "local_dir"))
