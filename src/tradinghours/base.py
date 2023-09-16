import datetime
from typing import Any, Generic, List, TypeVar, cast

from tradinghours.structure import OlsonTimezone

T = TypeVar("T")


class BaseObject:
    """Base model objects"""

    def __init__(self):
        self.data = {}


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
