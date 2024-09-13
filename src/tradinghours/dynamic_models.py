from typing import Union
from pprint import pprint
from sqlalchemy import func
import datetime as dt

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

        data = {k:v for k,v in data.items() if k != "id"}
        self._data = data
        _fields = []
        for key, value in data.items():
            if key == "observed":
                value = value == "OBS"

            setattr(self, key, value)
            _fields.append(key)

        exclude = set(dir(BaseModel))
        _extra_fields = [] # properties
        for att in dir(self):
            if (att[0] != "_" and
                    att not in exclude
                    and isinstance(getattr(self.__class__, att, None), property)
            ):
                _extra_fields.append(att)

        self.fields = _fields + _extra_fields
        self._fields = _fields
        self._extra_fields = _extra_fields

    @property
    def raw_data(self):
        return self._data.copy()

    def to_dict(self) -> dict:
        return {att: getattr(self, att) for att in self.fields}

    def pprint(self) -> None:
        pprint(self.to_dict(), sort_dicts=False)

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}({self._data!r})"


class MarketHoliday(BaseModel):
    _table = "holidays"
    @property
    def has_settlement(self):
        return self.settlement == 'Yes'

    @property
    def is_open(self):
        return self.status == 'Open'


class MicMapping(BaseModel):
    _table = "mic_mapping"


class CurrencyHoliday(BaseModel):
    _table = "currency_holidays"


class PhaseType(BaseModel):
    _table = "phases"
    @classmethod
    def as_dict(cls) -> dict[str, "PhaseType"]:
        return {pt.name: pt[1:] for pt in db.query(cls.table)}

    @property
    def is_open(self):
        return self.status == 'Open'


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
        # start, end = validate_range_args(
        #     validate_date_arg("start", start),
        #     validate_date_arg("end", end),
        # )
        if not self.in_force_start_date and not self.in_force_end_date:
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
            raise MissingDefinitionError(f"missing definition {season} - {year}")
        return cls(result)

#### Special Class that does not have a _table because
# the data is generated
class Phase(BaseModel):
    _table = None

    @property
    def has_settlement(self):
        return self.settlement == 'Yes'

    @property
    def is_open(self):
        return self.status == 'Open'
