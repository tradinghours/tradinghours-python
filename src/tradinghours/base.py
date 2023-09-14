import datetime
from typing import Generic, TypeVar

T = TypeVar("T")


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


class BaseObject:
    """Base model objects"""

    def __init__(self):
        self.data = {}
