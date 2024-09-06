from typing import Union
from pprint import pprint
from .store import db


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


class Schedule(BaseModel):
    _table = "schedules"


class SeasonDefinition(BaseModel):
    _table = "season_definitions"


#### Special Class that does not have a _table because
# the data is generated
class Phase(BaseModel):
    _table = None