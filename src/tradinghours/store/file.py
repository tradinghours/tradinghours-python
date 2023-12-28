import csv
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple

from tradinghours.store.base import Cluster, Collection, Registry
from tradinghours.typing import StrOrPath
from tradinghours.validate import validate_path_arg


class FileCluster(Cluster):
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
        next_key = 1
        with open(self.location, "r", encoding="utf-8", newline="") as file:
            for row in csv.reader(file):
                key = row[0] or str(next_key)
                next_key += 1
                data = row[1:]
                if key:
                    keyed_items[key] = data
        return keyed_items


class FileClusterRegistry(Registry[FileCluster]):
    """Holds a series of file clusters"""

    def __init__(self, folder: StrOrPath):
        self._folder = validate_path_arg("folder", folder)
        super().__init__()

    @property
    def folder(self) -> Path:
        return self._folder

    def create(self, slug: str) -> FileCluster:
        location = self.folder / f"{slug}.dat"
        return FileCluster(location)

    def discover(self) -> Generator[str, None, None]:
        if self.folder.exists():
            for item in self.folder.iterdir():
                if item.is_file():
                    yield item.stem


class FileCollection(Collection):
    """Manages a collection of items in a store"""

    def __init__(self, folder: StrOrPath):
        self._folder = validate_path_arg("folder", folder)
        self._clusters = FileClusterRegistry(folder)

    @property
    def folder(self) -> Path:
        return self._folder

    @property
    def clusters(self) -> FileClusterRegistry:
        return self._clusters

    def touch(self):
        self.folder.mkdir(exist_ok=True)

    def clear(self):
        for current in self._clusters:
            current.truncate()
        self._clusters = FileClusterRegistry(self.folder)


class FileCollectionRegistry(Registry[FileCollection]):
    """Holds a series of collections"""

    def __init__(self, root: StrOrPath):
        self._root = validate_path_arg("root", root)
        super().__init__()

    @property
    def root(self) -> Path:
        return self._root

    def create(self, slug: str) -> FileCollection:
        folder = self.root / slug
        collection = FileCollection(folder)
        collection.touch()
        return collection

    def discover(self) -> Generator[str, None, None]:
        if self.root.exists():
            for item in self.root.iterdir():
                if item.is_dir():
                    yield item.name
