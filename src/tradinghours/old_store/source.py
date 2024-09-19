import csv
from pathlib import Path
from typing import Generator, Generic, Type, TypeVar

from ..base import BaseObject
from ..typing import StrOrPath
from ..validate import (
    validate_path_arg,
    validate_str_arg,
    validate_subclass_arg,
)

B = TypeVar("B", bound=BaseObject)


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
