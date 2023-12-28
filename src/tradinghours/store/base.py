from abc import ABC, abstractmethod, abstractproperty
from typing import Dict, Generic, Iterator, List, Optional, Tuple, TypeVar

from ..util import slugify

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

    @abstractmethod
    def discover(self) -> Iterator[str]:
        raise NotImplementedError()

    def __iter__(self) -> Iterator[T]:
        return iter(self._resources.values())


class Cluster(ABC):
    """Generic Cluster interface"""

    def __init__(self, cache_size: Optional[int] = None):
        self._cached: List[str, Tuple] = []
        self._cache_size = cache_size or self.DEFAULT_CACHE_SIZE

    @abstractmethod
    def truncate(self):
        """Clear all elements from this cluster"""
        raise NotImplementedError()

    def append(self, key: Optional[str], data: Tuple):
        """Appends one element to this cluster

        Calling this method does not indicate that the data will be saved in
        the underlying storage. You need to call `flush` for that.

        """
        record = [key, data]
        self._cached.append(record)
        if len(self._cached) >= self._cache_size:
            self.flush()

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
