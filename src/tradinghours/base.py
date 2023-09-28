import csv
import datetime
from typing import Any, Dict, Generator, Generic, List, Self, TypeVar, cast

from .structure import FinId, Mic, OlsonTimezone, Weekday, WeekdayPeriod
from .util import snake_dict

T = TypeVar("T")


class BaseObject:
    """Base model objects"""

    def __init__(self, data: Dict):
        self.data = data

    @classmethod
    def from_csv(cls, csv_file_path) -> Generator[Self]:
        with open(csv_file_path, "r") as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                data = snake_dict(row)
                yield cls(data)


class Field(Generic[T]):
    """Base field class"""

    def __set_name__(self, owner, name):
        self.field_name = name

    def __get__(self, obj, objtype=None) -> T:
        if obj is None:
            return self
        value = obj.data[self.field_name]
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
