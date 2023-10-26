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

from .exceptions import PrepareError
from .structure import FinId, Mic, OlsonTimezone, Weekday, WeekdayPeriod, WeekdaySet
from .util import snake_case, snake_dict

if TYPE_CHECKING:
    from .catalog import Catalog

T = TypeVar("T")


class BaseObject:
    """Base model objects"""

    def __init__(self, data: Dict):
        self.data = data

    def to_dict(self) -> Dict:
        return self.data

    def to_tuple(self) -> Tuple:
        all_values = []
        for current_field in self.fields:
            current_value = getattr(self, current_field.field_name)
            all_values.append(current_value)
        return tuple(all_values)

    @classmethod
    def from_tuple(cls, data: Tuple):
        data_dict = {}
        for index, current_field in enumerate(cls.fields):
            current_value = data[index]
            data_dict[current_field.field_name] = current_value
        return cls(data_dict)

    @classmethod
    def from_dict(cls, data: Dict):
        normalized = snake_dict(data)
        return cls(normalized)

    @classmethod
    def get_catalog(cls, catalog: Optional["Catalog"]) -> "Catalog":
        if catalog is None:
            from .catalog import default_catalog

            return default_catalog
        return catalog

    def __str__(self):
        class_name = self.__class__.__name__
        return f"{class_name} {self.to_tuple()}"


class Field(Generic[T]):
    """Base field class"""

    def __set_name__(self, owner: Type[BaseObject], name):
        if not hasattr(owner, "fields"):
            owner.fields: List["Field"] = []
        owner.fields.append(self)
        self.field_name = name

    def __get__(self, obj, objtype=None) -> T:
        if obj is None:
            return self
        key = self.field_name
        if key in obj.data:
            value = obj.data[key]
        else:
            key = snake_case(objtype.__name__) + "_" + key
            value = obj.data.get(key, None)
        if value is None or value == "":
            return None
        else:
            return self.safe_prepare(value)

    def safe_prepare(self, value: str) -> T:
        try:
            return self.prepare(value)
        except Exception as error:
            raise PrepareError(self, value, inner=error)

    def prepare(self, value: str) -> T:
        return cast(T, value)


class StringField(Field[str]):
    """Field of string type"""

    pass


class BooleanField(Field[bool]):
    """Field of boolean type"""

    pass


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

    def prepare(self, value: str) -> OlsonTimezone:
        return OlsonTimezone.from_string(value)


class WeekdayField(Field[Weekday]):
    """Field for a Weekday"""

    def prepare(self, value: str) -> Weekday:
        return Weekday.from_string(value)


class WeekdayPeriodField(Field[WeekdayPeriod]):
    """Field for period like Mon-Fri"""

    def prepare(self, value: str) -> Weekday:
        return WeekdayPeriod.from_string(value)


class WeekdaySetField(Field[WeekdaySet]):
    """Field for set of periods like Mon-Fri"""

    def prepare(self, value: str) -> WeekdaySet:
        return WeekdaySet.from_string(value)


class FinIdField(Field[FinId]):
    """Field for a FinID"""

    def prepare(self, value: str) -> FinId:
        return FinId.from_string(value)


class MicField(Field[Mic]):
    """Field for a MIC"""

    def prepare(self, value: str) -> Mic:
        return Mic.from_string(value)
