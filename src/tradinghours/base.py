import csv
import datetime
from typing import Any, Dict, Generator, Generic, List, Self, TypeVar, cast

from .structure import FinId, Mic, OlsonTimezone, Weekday, WeekdayPeriod
from .typing import StrOrPath
from .util import snake_case, snake_dict

T = TypeVar("T")


class BaseObject:
    """Base model objects"""

    def __init__(self, data: Dict):
        self.data = data

    def to_dict(self) -> Dict:
        return self.data

    @classmethod
    def from_csv(cls, path: StrOrPath) -> Generator[Self, None, None]:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as file:
            reader = csv.DictReader(file)
            for row in reader:
                data = snake_dict(row)
                yield cls(data)


class Field(Generic[T]):
    """Base field class"""

    def __set_name__(self, owner, name):
        self.field_name = name

    def __get__(self, obj, objtype=None) -> T:
        if obj is None:
            return self
        key = self.field_name
        if key in obj.data:
            value = obj.data[key]
        else:
            key = snake_case(objtype.__name__) + "_" + key
            value = obj.data[key]
        return self.prepare(value)

    def prepare(self, value: Any) -> T:
        return cast(T, value)


class StringField(Field[str]):
    """Field of string type"""

    pass


class BooleanField(Field[bool]):
    """Field of boolean type"""

    pass


class DateField(Field[datetime.date]):
    """Field of date type"""

    pass


class DateTimeField(Field[datetime.datetime]):
    """Field of datetime type"""

    pass


class TimeField(Field[datetime.time]):
    """Field of time type"""

    pass


class ReferenceField(Field[BaseObject]):
    """Field for referencing other BaseObject children"""

    def __init__(self, referenced_type):
        super().__init__()
        self.referenced_type = referenced_type


class ListField(Field[List[T]]):
    """Field of a list with specific type"""

    pass


class OlsonTimezoneField(Field[OlsonTimezone]):
    """Field of an Olson Timezone"""

    def prepare(self, value) -> OlsonTimezone:
        return OlsonTimezone.from_string(value)


class WeekdayField(Field[Weekday]):
    """Field for a Weekday"""

    def prepare(self, value) -> Weekday:
        return Weekday.from_string(value)


class WeekdayPeriodField(Field[WeekdayPeriod]):
    """Field for period like Mon-Fri"""

    def prepare(self, value) -> Weekday:
        return WeekdayPeriod.from_string(value)


class FinIdField(Field[FinId]):
    """Field for a FinID"""

    def prepare(self, value) -> FinId:
        return FinId.from_string(value)


class MicField(Field[Mic]):
    """Field for a MIC"""

    def prepare(self, value) -> Mic:
        return Mic.from_string(value)
