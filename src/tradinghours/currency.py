from typing import List, Self

from .base import (
    BaseObject,
    BooleanField,
    DateField,
    OlsonTimezoneField,
    StringField,
    WeekdaySetField,
)


class Currency(BaseObject):
    """A currency supported by TradingHours."""

    code = StringField()
    """3-letter code of the currency (ISO 4217)."""

    name = StringField()
    """English name of the currency."""

    country_code = StringField()
    """2-letter country code for the currency's country."""

    central_bank = StringField()
    """Name of the central bank for the currency."""

    financial_capital = StringField()
    """City where the central bank is located."""

    financial_capital_timezone = OlsonTimezoneField()
    """Timezone Olson timezone identifier format."""

    weekend = WeekdaySetField()
    """Weekend definition. Most markets are Sat-Sun."""

    def list_holidays(self, start, end, catalog=None) -> "CurrencyHoliday":
        catalog = self.get_catalog(catalog)
        holidays = list(
            catalog.filter(
                CurrencyHoliday,
                cluster=self.currency_code,
                key_from=start,
                key_to=end,
            )
        )
        return holidays

    @classmethod
    def list_all(cls, catalog=None) -> List[Self]:
        catalog = cls.get_catalog(catalog)
        return list(catalog.list_all(Currency))

    @classmethod
    def get(cls, code, catalog=None) -> "Currency":
        catalog = cls.get_catalog(catalog)
        return catalog.get(cls, code)


class CurrencyHoliday(BaseObject):
    """Holiday for an specific currency"""

    currency_code = StringField()
    """3-letter code of the currency (ISO 4217)."""

    date = DateField()
    """Shows the date of the holiday for the currency."""

    name = StringField()
    """Describes the name of the holiday."""

    has_settlement = BooleanField()
    """Whether the market has settlement for the holiday."""

    observed = BooleanField()
    """Whether the holiday is observed."""

    memo = StringField()
    """A description or additional details about the holiday, if applicable."""
