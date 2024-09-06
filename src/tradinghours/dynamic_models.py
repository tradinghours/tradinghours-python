from typing import Union
from pprint import pprint
from sqlalchemy import func

from .typing import StrOrDate
from .store import db
from .validate import validate_str_arg, validate_int_arg, validate_range_args, validate_date_arg
from .exceptions import MissingDefinitionError


class BaseModel:
    _table: Union[str, None] = None

    @classmethod
    @property
    def table(cls):
        return db.table(cls._table)

    def __init__(self, data: Union[dict, tuple]):
        if not isinstance(data, dict):
            data = {
                col_name: value for col_name, value in zip(
                    self.table.c.keys(), data
                )
            }

        self._data = data
        for key, value in data.items():
            setattr(self, key, value)

    def to_dict(self) -> dict:
        return self._data.copy()

    def pprint(self) -> None:
        pprint(self.to_dict(), sort_dicts=False)

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}({self._data!r})"


class MarketHoliday(BaseModel):
    _table = "holidays"


class MicMapping(BaseModel):
    _table = "mic_mapping"


class CurrencyHoliday(BaseModel):
    _table = "currency_holidays"


class PhaseType(BaseModel):
    _table = "phases"
    @classmethod
    def as_dict(cls) -> dict[str, "PhaseType"]:
        return {pt.name: pt for pt in db.query(cls)}


class Schedule(BaseModel):
    _table = "schedules"

    @classmethod
    def is_group_open(cls, group):
        # TODO: implement a ScheduleGroup type and consider other open groups
        return group.lower() == "regular"

    @property
    def has_season(self) -> bool:
        season_start = (self.season_start or "").strip()
        season_end = (self.season_end or "").strip()
        return bool(season_start and season_end)

    def is_in_force(self, start: StrOrDate, end: StrOrDate) -> bool:
        start, end = validate_range_args(
            validate_date_arg("start", start),
            validate_date_arg("end", end),
        )
        if self.in_force_start_date is None and self.in_force_end_date is None:
            return True
        elif self.in_force_start_date is None:
            return self.in_force_end_date >= start
        elif self.in_force_end_date is None:
            return self.in_force_start_date <= end
        else:
            return self.in_force_start_date <= end and self.in_force_end_date >= start

class SeasonDefinition(BaseModel):
    _table = "season_definitions"

    @classmethod
    def get(cls, season: str, year: int) -> "SeasonDefinition":
        season = validate_str_arg("season", season)
        year = validate_int_arg("year", year)

        table = cls.table
        result = db.query(table).filter(
            func.lower(table.c["season"]) == season.lower(),
            table.c["year"] == year
        ).one_or_none()

        if not result:
            raise MissingDefinitionError
        return cls(result)

#### Special Class that does not have a _table because
# the data is generated
class Phase(BaseModel):
    _table = None