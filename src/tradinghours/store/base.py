import os
from abc import ABC, abstractmethod, abstractproperty
from pathlib import Path
from typing import Dict, Generic, Iterator, Optional, Tuple, TypeVar

from tradinghours.store.file import FileCollectionRegistry

from ..base import BaseObject
from ..config import main_config
from ..typing import StrOrPath
from ..util import slugify
from ..validate import validate_path_arg

B = TypeVar("B", bound=BaseObject)
T = TypeVar("T")


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


class Cluster(ABC):
    """Generic Cluster interface"""

    @abstractmethod
    def truncate(self):
        """Clear all elements from this cluster"""
        raise NotImplementedError()

    @abstractmethod
    def append(self, key: Optional[str], data: Tuple):
        """Appends one element to this cluster

        Calling this method does not indicate that the data will be saved in
        the underlying storage. You need to call `flush` for that.

        """
        raise NotImplementedError()

    @abstractmethod
    def flush(self):
        """Flushes data to the underlying storage"""
        raise NotImplementedError()

    @abstractmethod
    def load_all(self) -> Dict[str, Tuple]:
        """Loads all data from this cluster"""
        raise NotImplementedError()


class Collection(ABC):
    """Generic Collection interface"""

    @abstractproperty
    def clusters(self) -> Registry:
        """Gets the clusters registry for this collection"""
        raise NotImplementedError()

    @abstractmethod
    def touch(self):
        """Ensure the collection exists"""
        raise NotImplementedError()

    @abstractmethod
    def clear(self):
        """Wipes all clusters in this collection"""
        raise NotImplementedError()


class Store:
    """Manages data loaded into memory"""

    def __init__(self, root: StrOrPath, collections_registry: FileCollectionRegistry):
        self._root = validate_path_arg("root", root)
        self.touch()
        self._collections = collections_registry

    @property
    def root(self) -> Path:
        return self._root

    @property
    def collections(self) -> FileCollectionRegistry:
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
