import datetime
from datetime import timedelta
from typing import Dict, Generator, Iterable, List, Tuple

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

# Arbitrary max offset days for TradingHours data
MAX_OFFSET_DAYS = 2


class Market(BaseObject):
    """One known market for TradingHours"""

    fin_id = FinIdField()
    """The FinID for the market."""

    exchange_name = StringField()
    """The exchange name of the market."""

    market_name = StringField()
    """The name of the market."""

    products = StringField()
    """Description of the products or securities group."""

    mic = MicField()
    """The MIC for the market."""

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

    @property
    def country_code(self):
        """Two-letter country code."""
        return self.fin_id.country

    def _pick_schedule_group(
        self,
        some_date: datetime.date,
        holidays: Dict[datetime.date, "MarketHoliday"],
    ) -> Tuple[str, bool]:
        if found := holidays.get(some_date):
            schedule_group = found.schedule.lower()
            fallback = Schedule.is_group_open(schedule_group)
        else:
            schedule_group = "regular"
            fallback = False
        return schedule_group, fallback

    def _filter_schedule_group(
        self, schedule_group: str, schedules: Iterable[Schedule]
    ) -> Iterable[Schedule]:
        for current in schedules:
            if current.schedule_group.lower() == schedule_group:
                yield current

    def _filter_inforce(
        self, some_date: datetime.date, schedules: Iterable[Schedule]
    ) -> Iterable[Schedule]:
        for current in schedules:
            if current.is_in_force(some_date, some_date):
                yield current

    def _filter_season(
        self, some_date: datetime.date, schedules: Iterable[Schedule]
    ) -> Iterable[Schedule]:
        for current in schedules:
            if current.match_season(some_date):
                yield current

    def _filter_weekdays(
        self, some_date: datetime.date, schedules: Iterable[Schedule]
    ) -> Iterable[Schedule]:
        for current in schedules:
            if current.days.matches(some_date):
                yield current

    def generate_schedules(
        self, start: StrOrDate, end: StrOrDate, catalog=None
    ) -> Generator[ConcretePhase, None, None]:
        start, end = validate_range_args(
            validate_date_arg("start", start),
            validate_date_arg("end", end),
        )
        catalog = self.get_catalog(catalog)

        # Get required global data
        offset_start = start - timedelta(days=MAX_OFFSET_DAYS)
        all_schedules = Schedule.list_all(self.fin_id)
        holidays = MarketHoliday.build_keyed(self.fin_id, offset_start, end)

        # Iterate through all dates generating phases
        current_date = offset_start
        while current_date <= end:
            # Starts with all schedules
            schedules = all_schedules

            # Filter schedule group based on holiday if any
            schedule_group, fallback = self._pick_schedule_group(current_date, holidays)
            schedules = self._filter_schedule_group(schedule_group, schedules)

            # Filters what is in force or for expected season
            schedules = self._filter_inforce(current_date, schedules)
            schedules = self._filter_season(current_date, schedules)

            # Save for fallback and filter weekdays
            before_weekdays = list(schedules)
            found_schedules = list(self._filter_weekdays(current_date, before_weekdays))

            # Consider fallback if needed
            if not found_schedules and fallback:
                initial_weekday = current_date.weekday()
                fallback_weekday = 6 if initial_weekday == 0 else initial_weekday - 1
                fallback_schedules = []
                while not fallback_schedules and fallback_weekday != initial_weekday:
                    fallback_schedules = list(
                        filter(
                            lambda s: s.days.matches(fallback_weekday),
                            before_weekdays,
                        ),
                    )
                    fallback_weekday = (
                        6 if fallback_weekday == 0 else fallback_weekday - 1
                    )
                found_schedules = fallback_schedules

            # Sort based on start time and duration
            found_schedules = sorted(
                found_schedules,
                key=lambda s: (s.start, s.duration),
            )

            # Generate phases for current date
            for current_schedule in found_schedules:
                start_date = current_date
                end_date = current_date + timedelta(days=current_schedule.offset_days)

                # Filter out phases not finishing after start because we
                # began looking a few days ago to cover offset days
                if end_date >= start:
                    start_date_str = start_date.isoformat() + "T"
                    end_date_str = end_date.isoformat() + "T"
                    start_str = start_date_str + current_schedule.start.isoformat()
                    end_str = end_date_str + current_schedule.end.isoformat()
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

    @classmethod
    def list_all(cls, catalog=None) -> List["Market"]:
        catalog = cls.get_catalog(catalog)
        return list(catalog.list_all(Market))

    @classmethod
    def get_by_finid(cls, finid: StrOrFinId, follow=True, catalog=None) -> "Market":
        finid = validate_finid_arg("finid", finid)
        catalog = cls.get_catalog(catalog)
        found = catalog.get(Market, str(finid), cluster=finid.country)
        if found and found.replaced_by and follow:
            found = catalog.get(Market, str(found.replaced_by), cluster=finid.country)
        return found

    @classmethod
    def get_by_mic(cls, mic: str, follow=True, catalog=None) -> "Market":
        mic = validate_str_arg("mic", mic)
        catalog = cls.get_catalog(catalog)
        mapping = MicMapping.get(mic, catalog=catalog)
        if mapping:
            return cls.get_by_finid(mapping.fin_id, follow=follow)
        return None

    @classmethod
    def get(cls, identifier: str, follow=True, catalog=None) -> "Market":
        identifier = validate_str_arg("identifier", identifier)
        catalog = cls.get_catalog(catalog)
        if "." in identifier:
            found = cls.get_by_finid(identifier, follow=follow)
        else:
            found = cls.get_by_mic(identifier, follow=follow)
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

    @classmethod
    def list_range(
        cls, finid: StrOrFinId, start: StrOrDate, end: StrOrDate, catalog=None
    ) -> List["MarketHoliday"]:
        finid = validate_finid_arg("finid", finid)
        start, end = validate_range_args(
            validate_date_arg("start", start),
            validate_date_arg("end", end),
        )
        catalog = cls.get_catalog(catalog)
        holidays = list(
            catalog.filter(
                MarketHoliday,
                start.isoformat(),
                end.isoformat(),
                cluster=str(finid),
            )
        )
        return holidays

    @classmethod
    def build_keyed(
        cls, finid: StrOrFinId, start: StrOrDate, end: StrOrDate, catalog=None
    ) -> Dict[datetime.date, "MarketHoliday"]:
        holidays = cls.list_range(finid, start, end)
        keyed = {}
        for current in holidays:
            keyed[current.date] = current
        return keyed


class MicMapping(BaseObject):
    """Mapping from MIC to FinId"""

    mic = StringField()
    """Market Identification Code"""

    fin_id = FinIdField()
    """TradingHours FinId"""

    @classmethod
    def get(cls, mic: str, catalog=None) -> "MicMapping":
        mic = validate_str_arg("mic", mic)
        catalog = cls.get_catalog(catalog)
        return catalog.get(cls, mic)
