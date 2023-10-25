import datetime
from typing import TYPE_CHECKING, Any, Tuple, TypeVar

if TYPE_CHECKING:
    from .structure import FinId

T = TypeVar("T")


def validate_date_arg(name: str, value: Any) -> datetime.date:
    if value is None:
        raise ValueError(f"Missing {name}")
    if isinstance(value, str):
        value = datetime.date.fromisoformat(value)
    if not isinstance(value, datetime.date):
        raise TypeError(f"Invalid {name} type")
    return value


def validate_range_args(start: T, end: T) -> Tuple[T, T]:
    if end < start:
        raise ValueError("Invalid date range")
    return start, end


def validate_str_arg(name: str, value: Any) -> str:
    if value is None:
        raise ValueError(f"Missing {name}")
    if not isinstance(value, str):
        raise TypeError(f"Invalid {name} type")
    return value


def validate_finid_arg(name: str, value: Any) -> "FinId":
    from .structure import FinId

    if value is None:
        raise ValueError(f"Missing {name}")
    if isinstance(value, str):
        value = FinId.from_string(value)
    if not isinstance(value, FinId):
        raise TypeError(f"Invalid {name} type")
    return value
