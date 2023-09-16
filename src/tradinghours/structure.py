from dataclasses import dataclass


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
