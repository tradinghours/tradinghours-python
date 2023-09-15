import datetime
from typing import Generic, List, TypeVar

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
        return obj.data[self.field_name]


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
