import datetime
from datetime import timedelta
from typing import Dict, Generator, List

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
from .typing import StrOrDate, StrOrFinId
from .validate import (
    validate_date_arg,
    validate_finid_arg,
    validate_range_args,
    validate_str_arg,
)


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

    replaced_by = FinIdField()

    def generate_schedules(
        self, start: StrOrDate, end: StrOrDate, catalog=None
    ) -> Generator[ConcretePhase, None, None]:
        start, end = validate_range_args(
            validate_date_arg("start", start),
            validate_date_arg("end", end),
        )
        catalog = self.get_catalog(catalog)

        # Get schedules happening in the period to be considered
        schedules_listing = catalog.list(Schedule, cluster=str(self.fin_id))
        all_schedules: List[Schedule] = []
        for _, current in schedules_listing:
            if current.is_in_force(start, end):
                all_schedules.append(current)

        # Holidays work as exceptions to the rule
        holidays_listing = self.list_holidays(start, end)
        keyed_holidays: Dict[datetime.date, MarketHoliday] = {}
        for current in holidays_listing:
            keyed_holidays[current.date] = current

        # Iterate from start to end date, generating phases
        current_date = start
        while current_date <= end:
            # Find holiday for current date
            if holiday := keyed_holidays.get(current_date):
                schedule_group = holiday.schedule.lower()
                # TODO: instead of just regular, consider all "open" schedules
                if schedule_group.lower() == "regular":
                    fallback_past_weekday = True
                else:
                    fallback_past_weekday = False
            else:
                schedule_group = "regular"
                fallback_past_weekday = False

            # Get schedules for current date
            valid_schedules = all_schedules

            # Filter Schedule Group
            valid_schedules = list(
                filter(
                    lambda s: s.schedule_group.lower() == schedule_group,
                    valid_schedules,
                )
            )

            # Filter by season
            valid_schedules = list(
                filter(
                    lambda s: s.match_season(current_date),
                    valid_schedules,
                )
            )

            # Get all schedules occurring for this date, including past
            # dates based on offset
            happening_schedules = []
            for current_valid_schedule in valid_schedules:
                this_schedule_occurrences = current_valid_schedule.match_occurrences(
                    current_date
                )
                for occurrence_date in this_schedule_occurrences:
                    happening_tuple = (occurrence_date, current_valid_schedule)
                    happening_schedules.append(happening_tuple)

            # Consider fallback if needed
            if not happening_schedules and fallback_past_weekday:
                # TODO: Remember to collect all matching for the weekday
                initial_weekday = current_date.weekday()
                fallback_weekday = 6 if initial_weekday == 0 else initial_weekday - 1
                while not happening_schedules and fallback_weekday != initial_weekday:
                    happening_schedules = list(
                        map(
                            lambda s: (current_date, s),
                            filter(
                                lambda s: s.days.matches(fallback_weekday),
                                valid_schedules,
                            ),
                        )
                    )
                    fallback_weekday = (
                        6 if fallback_weekday == 0 else fallback_weekday - 1
                    )

            # Sort them by start date
            happening_schedules = sorted(
                happening_schedules,
                key=lambda t: (t[0], t[1].start, t[1].duration),
            )

            # Generate phases for current date
            for some_date, some_schedule in happening_schedules:
                date_str = some_date.isoformat() + "T"
                start_str = date_str + some_schedule.start.isoformat()
                end_str = date_str + some_schedule.end.isoformat()
                yield ConcretePhase(
                    dict(
                        phase_type=some_schedule.phase_type,
                        phase_name=some_schedule.phase_name,
                        phase_memo=some_schedule.phase_memo,
                        start=start_str,
                        end=end_str,
                    )
                )

            # Next date, please
            current_date += timedelta(days=1)

    def list_holidays(
        self, start: StrOrDate, end: StrOrDate, catalog=None
    ) -> List["MarketHoliday"]:
        start, end = validate_range_args(
            validate_date_arg("start", start),
            validate_date_arg("end", end),
        )
        catalog = self.get_catalog(catalog)
        holidays = list(
            catalog.filter(
                MarketHoliday,
                start.isoformat(),
                end.isoformat(),
                cluster=str(self.fin_id),
            )
        )
        return holidays

    @classmethod
    def list_all(cls, catalog=None) -> List:
        catalog = cls.get_catalog(catalog)
        return list(catalog.list_all(Market))

    @classmethod
    def get_by_finid(cls, finid: StrOrFinId, catalog=None) -> "Market":
        finid = validate_finid_arg("finid", finid)
        catalog = cls.get_catalog(catalog)
        found = catalog.get(Market, str(finid), cluster=finid.country)
        if found and found.replaced_by:
            found = catalog.get(Market, str(found.replaced_by), cluster=finid.country)
        return found

    @classmethod
    def get_by_mic(cls, mic: str, catalog=None) -> "Market":
        mic = validate_str_arg("mic", mic)
        catalog = cls.get_catalog(catalog)
        found = catalog.get(MicMapping, mic)
        if found:
            return cls.get_by_finid(found.fin_id)
        return None

    @classmethod
    def get(cls, identifier: str, catalog=None) -> "Market":
        identifier = validate_str_arg("identifier", identifier)
        catalog = cls.get_catalog(catalog)
        if "." in identifier:
            found = cls.get_by_finid(identifier)
        else:
            found = cls.get_by_mic(identifier)
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


class MicMapping(BaseObject):
    """Mapping from MIC to FinId"""

    mic = StringField()
    """Market Identification Code"""

    fin_id = FinIdField()
    """TradingHours FinId"""
