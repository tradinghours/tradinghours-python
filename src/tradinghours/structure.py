from dataclasses import dataclass, field


@dataclass
class OlsonTimezone:
    country: str
    city: str

    def __str__(self):
        return f"{self.country}/{self.city}"

    @classmethod
    def from_string(cls, input_string):
        country, city = input_string.split("/")
        return cls(country, city)


@dataclass
class Weekday:
    WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    ordinal: int

    @classmethod
    def from_string(cls, input_string):
        input_string = input_string.title()  # Convert to title case
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

    @classmethod
    def from_string(cls, input_string):
        input_string = input_string.title()  # Convert to title case
        if "-" in input_string and len(input_string) == 7:
            start, end = input_string.split("-")
            start_day = Weekday.from_string(start)
            end_day = Weekday.from_string(end)
            return cls(start_day, end_day)
        raise ValueError("Invalid weekday period string")

    def __str__(self):
        return f"{str(self.start_day)}-{str(self.end_day)}"


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
