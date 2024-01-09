from .base import BaseObject, DateField, IntegerField, StringField


class SeasonDefinition(BaseObject):
    """Seasonality information"""

    season = StringField()
    """Season entry or code"""

    year = IntegerField()
    """Year when this definition is value"""

    date = DateField()
    """Especific date for this year"""
