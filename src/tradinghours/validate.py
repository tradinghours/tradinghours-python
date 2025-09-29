import datetime as dt
from typing import Any, Optional, Tuple, TypeVar
from .exceptions import InvalidType, InvalidValue

T = TypeVar("T")


def validate_date_arg(name: str, value: Any) -> dt.date:
    if value is None:
        raise InvalidValue(f"Missing {name}")
    if isinstance(value, str):
        value = dt.date.fromisoformat(value)
    if type(value) is not dt.date:
        raise InvalidType(f"Invalid {name} type")
    return value


def validate_range_args(start: T, end: T) -> Tuple[T, T]:
    if end < start:
        raise InvalidValue("Invalid date range")
    return start, end


def validate_str_arg(name: str, value: Any, strip=True) -> str:
    if value is None:
        raise InvalidValue(f"Missing {name}")
    if not isinstance(value, str):
        raise InvalidType(f"Invalid {name} type")
    if strip:
        value = value.strip()
    return value


def validate_int_arg(name: str, value: Any, default: Optional[int] = None) -> int:
    if value is None:
        if default is None:
            raise InvalidValue(f"Missing {name}")
        else:
            value = default
    if not isinstance(value, int):
        raise InvalidType(f"Invalid {name} type")
    return value


def validate_finid_arg(value: Any) -> str:
    if value is None:
        raise InvalidValue(f"Missing FinID")
    if isinstance(value, str):
        segments = value.split(".")
        if len(segments) < 2:
            raise InvalidValue("Invalid FinID string")
    return value.upper()

def validate_mic_arg(value: Any) -> str:
    if value is None:
        raise InvalidValue(f"Missing MIC")
    if not isinstance(value, str):
        raise InvalidType(f"MIC needs to be a str")
    if not value.isalnum() or len(value) != 4:
        raise InvalidValue(f"Invalid MIC string")
    return value.upper()