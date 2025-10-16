from typing import List, Union
import datetime as dt

from .validate import validate_range_args, validate_date_arg, validate_str_arg
from .models import BaseModel, CurrencyHoliday
from .store import db
from .exceptions import NotAvailable

class Currency(BaseModel):
    _table = "currencies"
    _original_string_format = "Currency: {currency_code} {currency_name}"

    def __init__(self, data):
        super().__init__(data)
        self.currency_code = self._data["currency_code"]
        self.currency_name = self._data["currency_name"]
        self.country_code = self._data["country_code"]
        self.central_bank = self._data["central_bank"]
        self.financial_capital = self._data["financial_capital"]
        self.financial_capital_timezone = self._data["financial_capital_timezone"]
        self.weekend_definition = self._data["weekend_definition"]

    def list_holidays(
        self, start: Union[str, dt.date], end: Union[str, dt.date]
    ) -> List["CurrencyHoliday"]:
        start, end = validate_range_args(
            validate_date_arg("start", start),
            validate_date_arg("end", end),
        )
        table = CurrencyHoliday.table()
        result = db.query(table).filter(
            table.c.currency_code == self.currency_code,
            table.c.date >= start,
            table.c.date <= end
        )
        return [CurrencyHoliday(r) for r in result]

    @classmethod
    @db.check_access
    def list_all(cls) -> List["Currency"]:
        return [cls(r) for r in db.query(cls.table())]

    @classmethod
    def is_available(cls, code:str) -> bool:
        try:
            cls.get(code)
            return True
        except (NotAvailable):
            return False

    @classmethod
    @db.check_access
    def get(cls, code: str) -> "Currency":
        validate_str_arg("code", code)
        result = db.query(cls.table()).filter(
            cls.table().c.currency_code == code
        ).one_or_none()
        if result is None:
            raise NotAvailable(
                f"The currency '{code}' is either mistyped, not supported by TradingHours, or you do not have permission to access this currency. Please contact support@tradinghours.com for more information or requesting a new currency to be covered."
            )

        return cls(result)
