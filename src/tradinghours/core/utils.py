import sqlite3
import datetime as dt
import pandas as pd

from sqlalchemy import (
    Integer,
    Time,
    Date,
    Boolean,
    Text
)

SQL_TYPES = {
    "date": (Date, dt.date.fromisoformat),
    "bool": (Boolean, lambda v: v == "OBS"),
    "time": (Time, dt.time.fromisoformat),
    "int": (Integer, int),
    "text": (Text, str)
}
PANDAS_TYPES = {
    "date": "datetime64[ns]",
    "bool": "bool",
    "time": "timedelta64[ns]",
    "int": "Int64", # not int64 (numpy) since that is not nullable
    "text": "string",
}

FIELD_TYPES = {
    "date": "date",
    "observed": "bool",
    "start": "time",
    "end": "time",
    "offset_days": "int",
    "duration": "int",
    "min_start": "time",
    "max_start": "time",
    "min_end": "time",
    "max_end": "time",
    "in_force_start_date": "date",
    "in_force_end_date": "date",
    "year": "int",
}

ANALYSIS_FIELDS_SCHEDULES = [
    "fin_id",
    "start",
    "end",
    "duration",
    "offset_days",
    "schedule_group",
    "timezone",
    "in_force_start_date",
    "in_force_end_date",
    "season_start",
    "season_end",
    "days",
    "phase_type",
]

ANALYSIS_FIELDS_HOLIDAYS = ["fin_id", "date", "schedule"]

# for calculations I want specific columns

# for pipeline, I want all columns

# general types



def slugify(string):
    return string.lower().replace(" ", "_").replace("-", "_")


def set_types(data):
    """
    used to make sure pd.DataFrames are typed correctly
    """
    for title, df in data.items():
        for col in df:
            typ = FIELD_TYPES.get(col, "text")
            df[col] = df[col].astype(PANDAS_TYPES.get(typ))
    return data