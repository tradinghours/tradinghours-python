import datetime
from typing import List

from .season import SeasonDefinition

from ..base import (
    class_decorator,
    BooleanField,
    BaseObject,
    DateField,
    DateTimeField,
    FinIdField,
    IntegerField,
    ZoneInfoField,
    StringField,
    TimeField,
    WeekdaySetField,
)
from ..typing import StrOrDate, StrOrFinId
from ..validate import validate_date_arg, validate_finid_arg, validate_range_args

@class_decorator
class PhaseType(BaseObject):
    name = StringField()
    """The name of the phase type, mapped to phase_type in schedules"""

    status = StringField()
    """If this type of phase is considered open or closed"""

    settlement = StringField()
    """Whether settlement occurs during this type of phase"""

    @property
    def has_settlement(self):
        return self.settlement == 'Yes'

    @property
    def is_open(self):
        return self.status == 'Open'

    @classmethod
    def as_dict(cls, catalog=None) -> List["Schedule"]:
        catalog = cls.get_catalog(catalog)
        return {t[1].name: t[1] for t in catalog.list(cls)}

@class_decorator
class Phase(BaseObject):
    """A period within a schedule"""

    phase_type = StringField()
    """Well known options"""

    phase_name = StringField()
    """Describes the name for the phase type."""

    phase_memo = StringField()
    """If applicable, will have additional description or information."""

    status = StringField()
    """Describes what status the market is currently."""

    settlement = StringField()
    """Describes what status the market is currently."""

    start = DateTimeField()
    """The date the market phase type started."""

    end = DateTimeField()
    """The scheduled date for the market phase type to end."""

    _string_format = "{start} - {end} {phase_type}"

    @property
    def has_settlement(self):
        return self.settlement == 'Yes'

    @property
    def is_open(self):
        return self.status == 'Open'


@class_decorator
class Schedule(BaseObject):
    """Schedules definitions from TradingHours"""

    fin_id = FinIdField()
    schedule_group = StringField()
    schedule_group_memo = StringField()
    timezone = ZoneInfoField()
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

    _string_format = "{fin_id} ({schedule_group}) {start} - {end_with_offset} {days} {phase_type}"

    @property
    def end_with_offset(self):
        end = str(self.end)
        if self.offset_days:
            return end + f" +{self.offset_days}"
        return end + "   "

    @property
    def has_season(self) -> bool:
        season_start = (self.season_start or "").strip()
        season_end = (self.season_end or "").strip()
        return bool(season_start and season_end)

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

    def match_season(self, some_date: StrOrDate) -> bool:
        """Indicates whether some_date matches season if any"""
        some_date = validate_date_arg("some_date", some_date)

        # If there is no season, it means there is no restriction in terms
        # of the season when this schedule is valid, and as such it is valid,
        # from a season-perspective for any date
        if not self.has_season:
            return True

        start_date = SeasonDefinition.get_date(self.season_start, some_date.year)
        end_date = SeasonDefinition.get_date(self.season_end, some_date.year)
        if end_date < start_date:
            return some_date <= end_date or some_date >= start_date
        return some_date >= start_date and some_date <= end_date

    @classmethod
    def is_group_open(cls, group):
        # TODO: implement a ScheduleGroup type and consider other open groups
        return group.lower() == "regular"
