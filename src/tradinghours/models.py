from typing import Union
import pprint
from sqlalchemy import func
import datetime as dt

from .store import db
from .validate import validate_str_arg, validate_int_arg, validate_range_args, validate_date_arg
from .exceptions import MissingDefinitionError


class BaseModel:
    """
    Will receive records from the databse and set the instance attributes. The attributes
     match the column names and some classes have additional properties.

    Besides accessing the data through attributes like `market.exchange_name`,
     you can also access `data` or `to_dict`. See their docstrings to see how they differ.

    """
    _table: Union[str, None] = None
    _string_format: str = ""
    _original_string_format: str = ""
    _fields: list = [] # columns in database
    _extra_fields: list = []  # properties of python class
    _access_levels: set = set()

    @classmethod
    def table(cls) -> "Table":
        return db.table(cls._table)

    @classmethod
    def fields(cls):
        return cls._fields + cls._extra_fields

    def __init__(self, data: Union[dict, tuple]):
        if not isinstance(data, dict):
            data = {
                col_name: value for col_name, value in zip(
                    self.table().c.keys(), data
                )
            }

        self._data = {}
        _fields = []
        for key, value in data.items():
            if key != "id":
                setattr(self, key, value)
                self._data[key] = value
                _fields.append(key)

        if not self.__class__._fields:
            exclude = set(dir(BaseModel))
            _extra_fields = [] # properties
            for att in dir(self):
                if (att[0] != "_" and
                        att not in exclude
                        and isinstance(getattr(self.__class__, att, None), property)
                ):
                    _extra_fields.append(att)

            self.__class__._fields = _fields
            self.__class__._extra_fields = _extra_fields

    @property
    def data(self) -> dict:
        """
        Returns a dictionary with the values exactly as they were in the
         database, excluding properties like .is_open. Keys are exact matches to the
         column names of the matching table.
        """
        return {f: getattr(self, f) for f in self._fields}

    def to_dict(self) -> dict:
        """
        Returns a dictionary with the values as they are displayed to the user, including
         properties like .is_open, which means that there are keys present that don't exist
         in the matching table.
        """
        dct = {}
        for f in self.fields():
            dct[f] = getattr(self, f)
            dct[f] = dct[f].to_dict() if hasattr(dct[f], 'to_dict') else dct[f]
        return dct

    def pformat(self) -> str:
        dct = {}
        for f in self.fields():
            val = getattr(self, f)
            if not isinstance(val, int) and not isinstance(val, float) and val is not None:
                val = str(val)
            dct[f] = val
        return pprint.pformat(dct, sort_dicts=False)

    def pprint(self) -> None:
        print(self.pformat())

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}({self._data!r})"

    @classmethod
    def get_string_format(cls):
        return cls._string_format or cls._original_string_format

    @classmethod
    def set_string_format(cls, string_format: str, prefix_class: bool = False):
        if prefix_class:
            string_format = f"{cls.__name__}: " + string_format
        cls._string_format = string_format

    @classmethod
    def reset_string_format(cls):
        cls._string_format = cls._original_string_format

    def __str__(self):
        return self.get_string_format().format(**self.to_dict())


class MarketHoliday(BaseModel):
    _table = "holidays"
    _original_string_format = "MarketHoliday: {fin_id} {date} {holiday_name}"

    def __init__(self, data):
        super().__init__(data)
        self.fin_id = self._data["fin_id"]
        self.date = self._data["date"]
        self.holiday_name = self._data["holiday_name"]
        self.schedule = self._data["schedule"]
        self.settlement = self._data["settlement"]
        self.observed = self._data["observed"]
        self.memo = self._data["memo"]
        self.status = self._data["status"]

    @property
    def has_settlement(self):
        return self.settlement == 'Yes'

    @property
    def is_open(self):
        return self.status == 'Open'


class MicMapping(BaseModel):
    _table = "mic_mapping"
    _original_string_format = "MicMapping: {mic} {fin_id}"

    def __init__(self, data):
        super().__init__(data)
        self.mic = self._data["mic"]
        self.fin_id = self._data["fin_id"]


class CurrencyHoliday(BaseModel):
    _table = "currency_holidays"
    _original_string_format = "CurrencyHoliday: {currency_code} {date} {holiday_name}"

    def __init__(self, data):
        super().__init__(data)
        self.currency_code = self._data["currency_code"]
        self.date = self._data["date"]
        self.holiday_name = self._data["holiday_name"]
        self.settlement = self._data["settlement"]
        self.observed = self._data["observed"]
        self.memo = self._data["memo"]


class PhaseType(BaseModel):
    _table = "phases"

    def __init__(self, data):
        super().__init__(data)
        self.name = self._data["name"]
        self.status = self._data["status"]
        self.settlement = self._data["settlement"]
        self.closing_price = self._data["closing_price"]

    @classmethod
    def as_dict(cls) -> dict[str, "PhaseType"]:
        return {pt.name: cls(pt) for pt in db.query(cls.table())}

    @property
    def has_settlement(self):
        return self.settlement == 'Yes'

    @property
    def is_open(self):
        return self.status == 'Open'


class Schedule(BaseModel):
    _table = "schedules"
    _original_string_format = "Schedule: {fin_id} ({schedule_group}) {start} - {end_with_offset} {days} {phase_type}"

    def __init__(self, data):
        super().__init__(data)
        self.fin_id = self._data["fin_id"]
        self.schedule_group = self._data["schedule_group"]
        self.schedule_group_memo = self._data["schedule_group_memo"]
        self.timezone = self._data["timezone"]
        self.phase_type = self._data["phase_type"]
        self.phase_name = self._data["phase_name"]
        self.phase_memo = self._data["phase_memo"]
        self.days = self._data["days"]
        self.start = self._data["start"]
        self.end = self._data["end"]
        self.offset_days = self._data["offset_days"]
        self.duration = self._data["duration"]
        self.min_start = self._data["min_start"]
        self.max_start = self._data["max_start"]
        self.min_end = self._data["min_end"]
        self.max_end = self._data["max_end"]
        self.in_force_start_date = self._data["in_force_start_date"]
        self.in_force_end_date = self._data["in_force_end_date"]
        self.season_start = self._data["season_start"]
        self.season_end = self._data["season_end"]

    @property
    def end_with_offset(self):
        end = str(self.end)
        if self.offset_days:
            return end + f" +{self.offset_days}"
        return end + "   "

    @classmethod
    def is_group_open(cls, group):
        return group.lower() == "regular"

    @property
    def has_season(self) -> bool:
        season_start = (self.season_start or "").strip()
        season_end = (self.season_end or "").strip()
        return bool(season_start and season_end)

    def is_in_force(self, start: dt.date, end: dt.date) -> bool:
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
    _original_string_format = "SeasonDefinition: {date} {season}"

    def __init__(self, data):
        super().__init__(data)
        self.season = self._data["season"]
        self.year = self._data["year"]
        self.date = self._data["date"]

    @classmethod
    def get(cls, season: str, year: int) -> "SeasonDefinition":
        season = validate_str_arg("season", season)
        year = validate_int_arg("year", year)

        table = cls.table()
        result = db.query(table).filter(
            func.lower(table.c["season"]) == season.lower(),
            table.c["year"] == year
        ).one_or_none()

        if not result:
            raise MissingDefinitionError(f"missing definition {season} - {year}")
        return cls(result)


class Phase(BaseModel):
    _table = None
    _original_string_format = "Phase: {start} - {end} {phase_type}"

    def __init__(self, data):
        super().__init__(data)
        self.phase_type = self._data["phase_type"]
        self.phase_name = self._data["phase_name"]
        self.phase_memo = self._data["phase_memo"]
        self.status = self._data["status"]
        self.settlement = self._data["settlement"]
        self.start = self._data["start"]
        self.end = self._data["end"]
        self._timezone = str(self.start.tzinfo)

    @property
    def timezone(self):
        return self._timezone

    @property
    def has_settlement(self):
        return self.settlement == 'Yes'

    @property
    def is_open(self):
        return self.status == 'Open'


class MarketStatus(BaseModel):
    _table = None
    _original_string_format = "MarketStatus: {status}"

    def __init__(self, data):
        super().__init__(data)
        self.status = self._data["status"]
        self.reason = self._data["reason"]
        self.until = self._data["until"]
        self.next_bell = self._data["next_bell"]
        self.phase = self._data["phase"]
        self.market = self._data["market"]
