import datetime
from typing import List, Tuple

from .base import (
    BaseObject,
    BooleanField,
    DateField,
    DateTimeField,
    FinIdField,
    IntegerField,
    ListField,
    OlsonTimezoneField,
    StringField,
    TimeField,
    WeekdayField,
    WeekdaySetField,
)
from .typing import StrOrDate
from .validate import validate_date_arg, validate_int_arg, validate_range_args


class ConcretePhase(BaseObject):
    """A period within a schedule"""

    phase_type = StringField()
    """Well known options"""

    phase_name = StringField()
    """Describes the name for the phase type."""

    phase_memo = StringField()
    """If applicable, will have additional description or information."""

    status = StringField()
    """Describes what status the market is currently."""

    start = DateTimeField()
    """The date the market phase type started."""

    end = DateTimeField()
    """The scheduled date for the market phase type to end."""


class DateSchedule(BaseObject):
    """Full trading schedule for a market on a specific date"""

    date = DateField()
    """The date for the data returned."""

    day_of_week = WeekdayField()
    """The day of the week for the data returned."""

    is_open = BooleanField()
    """Describes in true/false statement if the market is open."""

    has_settlement = BooleanField()
    """Describes in true/false statement if the market has settlement."""

    holiday = StringField()
    """Describes the holiday, if any."""

    schedule = ListField[ConcretePhase]()
    """Nested data of the schedule."""


class PeriodSchedule(BaseObject):
    """Market phases for a given period"""

    start = DateTimeField()
    """The start date for the data returned."""

    end = DateTimeField()
    """The end date for the data returned."""

    schedule = ListField[ConcretePhase]()
    """Nested data of the schedule."""


class Schedule(BaseObject):
    """Schedules definitions from TradingHours"""

    fin_id = FinIdField()
    schedule_group = StringField()
    schedule_group_memo = StringField()
    timezone = OlsonTimezoneField()
    phase_type = StringField()
    phase_name = StringField()
    phase_memo = StringField()
    days = WeekdaySetField()
    start = TimeField()
    end = TimeField()
    offset_days = IntegerField()
    duration = StringField()
    min_start = TimeField()
    max_start = TimeField()
    min_end = TimeField()
    max_end = TimeField()
    in_force_start_date = DateField()
    in_force_end_date = DateField()
    season_start = StringField()
    season_end = StringField()

    def is_in_force(self, start: StrOrDate, end: StrOrDate) -> bool:
        start, end = validate_range_args(
            validate_date_arg("start", start),
            validate_date_arg("end", end),
        )
        if self.in_force_start_date is None and self.in_force_end_date is None:
            return True
        elif self.in_force_start_date is None:
            return self.in_force_end_date >= start
        elif self.in_force_end_date is None:
            return self.in_force_start_date <= end
        else:
            return self.in_force_start_date <= end and self.in_force_end_date >= start

    def match_occurrences(self, some_date: StrOrDate) -> List[datetime.date]:
        """This method will return all matches for one single date"""
        some_date = validate_date_arg("some_date", some_date)

        # Keep track of all dates matching some_date, considering the offset
        # for previous dates could match this date too
        occurrences: List[datetime.date] = []

        # We will scan all dates considering the offset
        current_date = some_date
        current_offset = self.offset_days
        while current_offset >= 0:
            # Check whether it happens on this specific date
            happens = self.is_in_force(current_date, current_date)
            happens = happens and self.days.matches(current_date)
            if happens:
                occurrences.append(current_date)

            # Prepare to match now the previous date
            current_date -= datetime.timedelta(days=1)
            current_offset -= 1

        # Return all occurences
        return occurrences

    @classmethod
    def list_all(cls, catalog=None) -> List:
        catalog = cls.get_catalog(catalog)
        return list(catalog.list_all(Schedule))


class RegularSchedule(BaseObject):
    """Repeating schedule for a market"""

    day = WeekdayField()
    """Day of the week in string format."""

    open = BooleanField()
    """Describes if the market is open in true/false."""

    time_start = TimeField()
    """Describes the time the market trading session opens."""

    time_end = TimeField()
    """Describes the time the market trading session ends."""

    lunch = BooleanField()
    """Describes if the market has observed lunch hours in true/false."""

    lunch_start = TimeField()
    """If observed lunch hours, this describes when lunch hours start."""

    lunch_end = TimeField()
    """If observing lunch hours, this describes when lunch hours end."""

    pre_hours_start = TimeField()
    """If pre-hours, describes what time they start."""

    pre_hours_end = TimeField()
    """If pre-hours, describes what time they end."""

    post_hours_start = TimeField()
    """If post-hours, describes what time they start."""

    post_hours_end = TimeField()
    """If post-hours, describes what time they end."""
