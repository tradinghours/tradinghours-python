from dataclasses import dataclass, field
from typing import List, Tuple

from .typing import WeekdaySpec
from .validate import validate_weekday_arg

@dataclass
class Weekday:
    WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    ordinal: int

    def next(self) -> "Weekday":
        if self.ordinal == 6:
            return Weekday(0)
        return Weekday(self.ordinal + 1)

    def previous(self) -> "Weekday":
        if self.ordinal == 0:
            return Weekday(6)
        return Weekday(self.ordinal - 1)

    @classmethod
    def from_string(cls, input_string):
        input_string = input_string.title()
        if input_string in cls.WEEKDAYS:
            return cls(cls.WEEKDAYS.index(input_string))
        else:
            raise ValueError("Invalid weekday string")

    def __str__(self):
        return self.WEEKDAYS[self.ordinal]


@dataclass
class WeekdayPeriod:
    start_day: Weekday
    end_day: Weekday

    @property
    def weekdays(self) -> List:
        captured = []
        current_day = self.start_day.previous()
        finished = False
        while not finished:
            current_day = current_day.next()
            captured.append(current_day)
            if current_day == self.end_day:
                finished = True
        return captured

    def matches(self, other: WeekdaySpec) -> bool:
        other = validate_weekday_arg("other", other)
        return other in self.weekdays

    @classmethod
    def from_string(cls, input_string):
        if "-" in input_string:
            start, end = input_string.split("-")
            start_day = Weekday.from_string(start)
            end_day = Weekday.from_string(end)
            return cls(start_day, end_day)
        else:
            only_day = Weekday.from_string(input_string)
            return cls(only_day, only_day)

    def __str__(self):
        if self.start_day == self.end_day:
            return str(self.start_day)
        else:
            return f"{str(self.start_day)}-{str(self.end_day)}"


@dataclass
class WeekdaySet:
    periods: Tuple[WeekdayPeriod]

    def matches(self, other: WeekdaySpec) -> bool:
        other = validate_weekday_arg("other", other)
        for current in self.periods:
            if current.matches(other):
                return True
        return False

    @classmethod
    def from_string(cls, input_string):
        all_period_str = input_string.split(",")
        all_period = []
        for period_str in all_period_str:
            period = WeekdayPeriod.from_string(period_str)
            all_period.append(period)
        return cls(tuple(all_period))

    def __str__(self):
        periods = [str(p) for p in self.periods]
        return ",".join(periods)


@dataclass
class FinId:
    country: str
    acronym: str
    extra: list = field(default_factory=list)

    def __post_init__(self):
        self.country = self.country.upper()
        self.acronym = self.acronym.upper()
        self.extra = [e.upper() for e in self.extra]

    @classmethod
    def from_string(cls, input_string):
        segments = input_string.split(".")
        if len(segments) < 2:
            raise ValueError("Invalid FinID string")
        return cls(segments[0], segments[1], segments[2:])

    def __str__(self):
        segments = [self.country, self.acronym] + self.extra
        return ".".join(segments)


@dataclass
class Mic:
    code: str

    def __post_init__(self):
        self.code = self.code.upper()

    @classmethod
    def from_string(cls, input_string):
        return cls(input_string)

    def __str__(self):
        return self.code
