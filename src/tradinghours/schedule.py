from tradinghours.base import (
    BaseObject,
    BooleanField,
    DateField,
    DateTimeField,
    FinIdField,
    ListField,
    OlsonTimezoneField,
    StringField,
    TimeField,
    WeekdayField,
)


# TODO: consider renaming to ConcretePhase because of phase_type
class Phase(BaseObject):
    """A period within a schedule"""

    type = StringField()
    """Well known options"""

    name = StringField()
    """Describes the name for the phase type."""

    memo = StringField()
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

    schedule = ListField[Phase]()
    """Nested data of the schedule."""


class PeriodSchedule(BaseObject):
    """Market phases for a given period"""

    start = DateTimeField()
    """The start date for the data returned."""

    end = DateTimeField()
    """The end date for the data returned."""

    schedule = ListField[Phase]()
    """Nested data of the schedule."""


class Schedule(BaseObject):

    fin_id = FinIdField()
    schedule_group = StringField()
    schedule_group_memo = StringField()
    timezone = OlsonTimezoneField()
    phase_type = 


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
