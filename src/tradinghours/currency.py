from typing import List, Union
import datetime as dt

from .validate import validate_range_args, validate_date_arg, validate_str_arg
from .models import BaseModel, CurrencyHoliday
from .store import db
from .exceptions import NotCovered, NoAccess

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
        except (NoAccess, NotCovered):
            return False

    @classmethod
    @db.check_access
    def is_covered(cls, code:str) -> bool:
        """
        Returns True or False showing if tradinghours provides data for the Currency.
        This differs from is_available because is_covered does not mean that the user
        has access to it under their current plan.
        """
        table = db.table("covered_currencies")
        found = db.query(table).filter(
            table.c.currency_code == code
        ).one_or_none()
        return found is not None

    @classmethod
    @db.check_access
    def get(cls, code: str) -> "Currency":
        validate_str_arg("code", code)
        result = db.query(cls.table()).filter(
            cls.table().c.currency_code == code
        ).one_or_none()
        if result:
            return cls(result)

        if cls.is_covered(code):
            raise NoAccess(
                f"\n\nThe currency '{code}' is supported but not available on your current plan."
                f"\nPlease learn more or contact sales at https://www.tradinghours.com/data"
            )
        # if no result found, raise NotCovered
        raise NotCovered(
            f"The currency '{code}' is currently not available."
        )
