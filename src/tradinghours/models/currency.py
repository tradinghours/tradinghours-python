from typing import List

from ..base import (
    class_decorator,
    BaseObject,
    BooleanField,
    DateField,
    ZoneInfoField,
    StringField,
    WeekdaySetField,
)
from ..typing import StrOrDate
from ..validate import validate_date_arg, validate_range_args, validate_str_arg

@class_decorator
class Currency(BaseObject):
    """A currency supported by TradingHours."""

    currency_code = StringField()
    """3-letter code of the currency (ISO 4217)."""

    currency_name = StringField()
    """English name of the currency."""

    country_code = StringField()
    """2-letter country code for the currency's country."""

    central_bank = StringField()
    """Name of the central bank for the currency."""

    financial_capital = StringField()
    """City where the central bank is located."""

    financial_capital_timezone = ZoneInfoField()
    """Timezone Olson timezone identifier format."""

    weekend_definition = WeekdaySetField()
    """Weekend definition. Most markets are Sat-Sun."""

    _string_format = "{currency_code} {currency_name}"

    def list_holidays(
        self, start: StrOrDate, end: StrOrDate, catalog=None
    ) -> "CurrencyHoliday":
        start, end = validate_range_args(
            validate_date_arg("start", start),
            validate_date_arg("end", end),
        )
        catalog = self.get_catalog(catalog)
        holidays = list(
            catalog.filter(
                CurrencyHoliday,
                cluster=self.currency_code,
                key_start=start.isoformat(),
                key_end=end.isoformat(),
            )
        )
        return holidays

    @classmethod
    def list_all(cls, catalog=None) -> List["Currency"]:
        catalog = cls.get_catalog(catalog)
        return list(catalog.list_all(Currency))

    @classmethod
    def get(cls, code: str, catalog=None) -> "Currency":
        code = validate_str_arg("code", code)
        catalog = cls.get_catalog(catalog)
        return catalog.get(cls, code)

@class_decorator
class CurrencyHoliday(BaseObject):
    """Holiday for an specific currency"""

    currency_code = StringField()
    """3-letter code of the currency (ISO 4217)."""

    date = DateField()
    """Shows the date of the holiday for the currency."""

    holiday_name = StringField()
    """Describes the name of the holiday."""

    settlement = StringField()
    """Whether the market has settlement for the holiday."""

    observed = BooleanField({'OBS': True, '': False, None: False})
    """Whether the holiday is observed."""

    memo = StringField()
    """A description or additional details about the holiday, if applicable."""

    _string_format = "{currency_code} {date} {holiday_name}"

    @property
    def has_settlement(self):
        return self.settlement == 'Yes'
