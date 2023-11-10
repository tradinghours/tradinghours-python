import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .structure import FinId, Weekday


StrOrPath = Union[str, Path]
StrOrDate = Union[str, datetime.date]
StrOrFinId = Union[str, "FinId"]
WeekdaySpec = Union[str, int, datetime.date, datetime.datetime, "Weekday"]
