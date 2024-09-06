from typing import List

from .typing import StrOrDate
from .validate import validate_range_args, validate_date_arg
from .dynamic_models import BaseModel, CurrencyHoliday
from .store import db

class Currency(BaseModel):
    _table = "currencies"

    def list_holidays(
        self, start: StrOrDate, end: StrOrDate
    ) -> List["CurrencyHoliday"]:
        start, end = validate_range_args(
            validate_date_arg("start", start),
            validate_date_arg("end", end),
        )
        table = CurrencyHoliday.table
        result = db.query(table).filter(
            table.c["currency_code"] == self.currency_code,
            table.c["date"] >= start.isoformat(),
            table.c["date"] <= end.isoformat()
        )
        return [CurrencyHoliday(r) for r in result]

    @classmethod
    def list_all(cls) -> List["Currency"]:
        return [cls(r) for r in db.query(cls.table)]


    @classmethod
    def get(cls, code: str) -> "Currency":
        result = db.query(cls.table).filter(
            cls.table.c["currency_code"] == code
        ).one()
        return cls(result)