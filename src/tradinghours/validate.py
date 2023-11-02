import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Tuple, Type, TypeVar

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


def validate_str_arg(name: str, value: Any, strip=True) -> str:
    if value is None:
        raise ValueError(f"Missing {name}")
    if not isinstance(value, str):
        raise TypeError(f"Invalid {name} type")
    if strip:
        value = value.strip()
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


def validate_path_arg(name: str, value: Any) -> Path:
    if value is None:
        raise ValueError(f"Missing {name}")
    if isinstance(value, str):
        value = Path(value)
    if not isinstance(value, Path):
        raise TypeError(f"Invalid {name} type")
    return value


def validate_subclass_arg(name: str, value: Any, baseclass: Type[T]) -> Type[T]:
    if value is None:
        raise ValueError(f"Missing {name}")
    if not issubclass(value, baseclass):
        raise TypeError(f"Invalid {name} type")
    return value


def validate_instance_arg(name: str, value: Any, baseclass: Type[T]) -> T:
    if value is None:
        raise ValueError(f"Missing {name}")
    if not isinstance(value, baseclass):
        raise TypeError(f"Invalid {name} type")
    return value
