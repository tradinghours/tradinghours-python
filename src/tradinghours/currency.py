from tradinghours.base import BaseObject, BooleanField, DateField, StringField


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

    financial_capital_timezone = StringField()
    """Timezone Olson timezone identifier format."""

    weekend = StringField()
    """Weekend definition. Most markets are Sat-Sun."""


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
