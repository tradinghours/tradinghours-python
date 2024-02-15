import datetime
from typing import (
    TYPE_CHECKING,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    cast,
)

from zoneinfo import ZoneInfo
from .exceptions import PrepareError
from .structure import FinId, Mic, Weekday, WeekdayPeriod, WeekdaySet
from .util import snake_dict
from pprint import pprint

if TYPE_CHECKING:
    from .catalog import Catalog

T = TypeVar("T")

def class_decorator(cls):
    fields = []
    extra_fields = []
    for att_name in cls.__dict__:
        if att_name.startswith("_"):
            continue
        att = getattr(cls, att_name)
        if callable(att):
            continue

        if isinstance(att, property):
            extra_fields.append(att_name)
        else:
            fields.append(att_name)

    cls._fields = fields
    cls._extra_fields = extra_fields
    cls.fields = [*fields, *extra_fields]
    cls.set_string_format(cls._string_format, prefix_class=True)
    cls._original_string_format = cls.get_string_format()
    return cls


class BaseObject:
    """Base model objects"""

    fields = [] # set in class_decorator
    _string_format = "" # set in each
    _original_string_format = ""

    @classmethod
    def get_string_format(cls):
        return cls._string_format

    @classmethod
    def set_string_format(cls, string_format: str, prefix_class: bool = False):
        try:
            string_format.format(**{f: "test" for f in cls.fields})
        except Exception as e:
            print(string_format)
            raise ValueError("Invalid formatting string") from e

        if prefix_class:
            string_format = f"{cls.__name__}: " + string_format

        cls._string_format = string_format

    @classmethod
    def reset_string_format(cls):
        cls._string_format = cls._original_string_format

    @classmethod
    def from_tuple(cls, data: Tuple):
        """Used when reading from local/.../.dat for loading"""
        return cls(data)

    @classmethod
    def from_dict(cls, data: Dict):
        """Used when reading from remote/csv for ingestion"""
        normalized = snake_dict(data)
        return cls(normalized)

    @classmethod
    def get_catalog(cls, catalog: Optional["Catalog"]) -> "Catalog":
        if catalog is None:
            from .catalog import default_catalog

            return default_catalog
        return catalog

    def __init__(self, data: [Dict, tuple]):
        """
        Sets the instance attributes, prepared according to their type.
            self.data holds the values of the instance attributes.
            self.raw_data holds the values as they were retrieved from the files.
        """
        if data_is_dict := isinstance(data, dict):
            self.raw_data = data
        else:
            self.raw_data = {}

        self.data = {}
        # print(self.__class__)
        # print(self.__class__.fields)
        # print(data)
        for i, field in enumerate(self._fields):
            if data_is_dict:
                raw_value = data[field]
            else:
                raw_value = data[i]
                self.raw_data[field] = raw_value

            prepared_value = getattr(self, field).safe_prepare(raw_value)
            if isinstance(prepared_value, tuple):
                prepared_value, obj = prepared_value
                setattr(self, f"{field}_obj", obj)

            setattr(self, field, prepared_value)
            self.data[field] = prepared_value

    def to_dict(self) -> Dict:
        return {f: getattr(self, f) for f in self.fields}

    # TODO: remove from this, it should be specific to writing the data
    def _to_tuple(self, raw=False) -> Tuple:
        """Used when adding data to store for ingestion"""
        data = self.raw_data if raw else self.data
        return tuple(data[f] for f in self._fields)

    def pprint(self):
        pprint(self.to_dict(), sort_dicts=False)

    def __repr__(self):
        class_name = self.__class__.__name__
        return f"{class_name}({self.data!r})"

    def __str__(self):
        if not self._string_format:
            class_name = self.__class__.__name__
            all_str = []
            for current_field in self.fields:
                current_value = getattr(self, current_field)
                if current_value:
                    all_str.append(str(current_value))
            fields_str = " ".join(all_str)
            return f"{class_name} {fields_str}"

        all_data = {f: getattr(self, f) for f in self.fields}
        return self._string_format.format(**all_data)


class Field(Generic[T]):
    """Base field class"""
    def __set_name__(self, owner: Type[BaseObject], name):
        self._field_name = f"{owner}.{name}"

    def safe_prepare(self, value: str) -> T:
        if value in (None, ''):
            return None
        try:
            return self.prepare(value)
        except Exception as error:
            raise PrepareError(self, value, inner=error) from error

    def prepare(self, value: str) -> str:
        return value

class StringField(Field[str]):
    """Field of string type"""
    pass

class BooleanField(Field[bool]):
    """Field of boolean type"""

    def __init__(self, bool_mapping=None):
        self.bool_mapping = bool_mapping

    def safe_prepare(self, value: str) -> T:
        try:
            # print("trying to prepare", repr(value), self.bool_mapping)
            return self.prepare(value)
        except Exception as error:
            raise PrepareError(self, value, inner=error) from error

    def prepare(self, value: [str, bool]) -> [T, tuple]:
        if self.bool_mapping is None:
            assert isinstance(value, bool), f"Invalid type passed to BooleanField of {self._field_name}"
            return value
        return self.bool_mapping[value]


class IntegerField(Field[int]):
    """Field of int type"""

    def prepare(self, value: str) -> int:
        return int(value)


class DateField(Field[datetime.date]):
    """Field of date type"""

    def prepare(self, value: str) -> datetime.date:
        return datetime.date.fromisoformat(value)


class DateTimeField(Field[datetime.datetime]):
    """Field of datetime type"""

    def prepare(self, value: str) -> datetime.datetime:
        return datetime.datetime.fromisoformat(value)


class TimeField(Field[datetime.time]):
    """Field of time type"""

    def prepare(self, value: str) -> datetime.time:
        return datetime.time.fromisoformat(value)


class ListField(Field[List[T]]):
    """Field of a list with specific type"""
    pass


class ZoneInfoField(Field[ZoneInfo]):
    """Field of an Olson Timezone"""

    def prepare(self, value: str) -> Tuple[str, ZoneInfo]:
        return value, ZoneInfo(value)


class WeekdayField(Field[Weekday]):
    """Field for a Weekday"""

    def prepare(self, value: str) -> Tuple[str, Weekday]:
        return value, Weekday.from_string(value)


class WeekdayPeriodField(Field[WeekdayPeriod]):
    """Field for period like Mon-Fri"""

    def prepare(self, value: str) -> Tuple[str, Weekday]:
        return value, WeekdayPeriod.from_string(value)


class WeekdaySetField(Field[WeekdaySet]):
    """Field for set of periods like Mon-Fri"""

    def prepare(self, value: str) -> Tuple[str, WeekdaySet]:
        return value, WeekdaySet.from_string(value)


class FinIdField(Field[FinId]):
    """Field for a FinID"""

    def prepare(self, value: str) -> Tuple[str, FinId]:
        return value, FinId.from_string(value)


class MicField(Field[Mic]):
    """Field for a MIC"""

    def prepare(self, value: str) -> Tuple[str, Mic]:
        return value, Mic.from_string(value)
