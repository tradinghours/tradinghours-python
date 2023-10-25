import datetime
from datetime import timedelta
from typing import Generator, List, Self

from .base import (
    BaseObject,
    BooleanField,
    DateField,
    FinIdField,
    MicField,
    StringField,
    WeekdaySetField,
)
from .schedule import ConcretePhase, Schedule
from .structure import FinId


class Market(BaseObject):
    """One known market for TradingHours"""

    fin_id = FinIdField()
    """The FinID for the market."""

    country_code = StringField()
    """Two-letter country code."""

    exchange = StringField()
    """The exchange name of the market."""

    market = StringField()
    """The name of the market."""

    products = StringField()
    """Description of the products or securities group."""

    mic = MicField()
    """The MIC for the market."""

    mic_extended = StringField()
    """The extended MIC for the market."""

    acronym = StringField()
    """The acronym for the market."""

    asset_type = StringField()
    """Describes the asset type of the market."""

    memo = StringField()
    """A description or additional details about the trading venue."""

    permanently_closed = DateField()
    """If a market is permanently closed, this shows the date."""

    timezone = StringField()
    """Gives the timezone the market utilizes."""

    weekend_definition = WeekdaySetField()
    """Indicates the days of the week when the market regularly closed."""

    def generate_schedules(
        self, start, end, catalog=None
    ) -> Generator[ConcretePhase, None, None]:
        catalog = self.get_catalog(catalog)

        # Get schedules happening in the period to be considered
        schedules_listing = catalog.list(Schedule, cluster=str(self.fin_id))
        intersecting_schedules: List[Schedule] = []
        for _, current in schedules_listing:
            if current.intersects_with(start, end):
                intersecting_schedules.append(current)

        # Iterate from start to end date, generating phases
        current_date: datetime.date = start
        while current_date <= end:
            date_schedules = sorted(
                filter(
                    lambda fs: fs.happens_at(current_date),
                    intersecting_schedules,
                ),
                key=lambda ss: ss.start,
            )

            # Generate phases for current date
            for current_schedule in date_schedules:
                date_str = current_date.isoformat() + "T"
                start_str = date_str + current_schedule.start.isoformat()
                end_str = date_str + current_schedule.end.isoformat()
                yield ConcretePhase(
                    dict(
                        phase_type=current_schedule.phase_type,
                        phase_name=current_schedule.phase_name,
                        phase_memo=current_schedule.phase_memo,
                        start=start_str,
                        end=end_str,
                    )
                )

            # Next date, please
            current_date += timedelta(days=1)

    def list_holidays(
        self, start, end, catalog=None
    ) -> Generator["MarketHoliday", None, None]:
        catalog = self.get_catalog(catalog)
        holidays = list(
            catalog.filter(
                MarketHoliday,
                start,
                end,
                cluster=str(self.fin_id),
            )
        )
        return holidays

    @classmethod
    def list_all(cls, catalog=None) -> List:
        catalog = cls.get_catalog(catalog)
        return list(catalog.list_all(Market))

    @classmethod
    def get_by_fin_id(cls, fin_id: FinId, catalog=None) -> Self:
        found = catalog.get(Market, fin_id, cluster=fin_id.country)
        if found.replaced_by:
            found = catalog.get(Market, fin_id=found.replaced_by)
        return found


class MarketHoliday(BaseObject):
    """Holidays for a Market"""

    fin_id = FinIdField()
    """The FinID for the market."""

    date = DateField()
    """Shows the date of the holiday for the market."""

    name = StringField()
    """Describes the name of the holiday."""

    schedule = StringField()
    """Describes if the market closes for the holiday."""

    is_open = BooleanField()
    """Displays in true/false if the market is open for the holiday."""

    has_settlement = BooleanField()
    """Displays in true/false if the market has settlement for the holiday."""

    observed = BooleanField()
    """Displays in true/false if the holiday is observed."""

    memo = StringField()
    """A description or additional details about the holiday."""
