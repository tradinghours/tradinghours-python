import datetime

from ..base import BaseObject, DateField, IntegerField, StringField, class_decorator
from ..exceptions import MissingDefinitionError
from ..validate import validate_int_arg, validate_str_arg

@class_decorator
class SeasonDefinition(BaseObject):
    """Seasonality information"""

    season = StringField()
    """Season entry or code"""

    year = IntegerField()
    """Year when this definition is value"""

    date = DateField()
    """Especific date for this year"""

    _string_format = "{date} {season}"

    @classmethod
    def get(cls, season: str, year: int, catalog=None) -> "SeasonDefinition":
        season = validate_str_arg("season", season)
        year = validate_int_arg("year", year)
        catalog = cls.get_catalog(catalog)
        for _, definition in catalog.list(cls):
            if definition.season.lower() == season.lower() and definition.year == year:
                return definition
        raise MissingDefinitionError()

    @classmethod
    def get_date(cls, season: str, year: int, catalog=None) -> datetime.date:
        definition = cls.get(season, year)
        return definition.date
