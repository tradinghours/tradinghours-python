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

def get_pandas_type(col):
    return PANDAS_TYPES.get(FIELD_TYPES.get(col, "text"))

def fix_types_for_sql(df):
    """
    needs to ensure correct conversion for saving in sql
    without changing df in place or copying df if not necessary
    """
    td_cols = []
    for col in df:
        if "timedelta" in str(df[col].dtype):
            td_cols.append(col)

    if td_cols:
        df = df.copy()
        for col in td_cols:
            df[col] = df[col].astype("string").str.split("days ").str[-1]

    return df


def set_types(data):
    """
    used to make sure pd.DataFrames are typed correctly
    """
    for title, df in data.items():
        for col in df:
            df[col] = df[col].astype(get_pandas_type(col))
    return data

def create_seasondefs(season_definitions):
    season_definitions["season"] = season_definitions.season.str.lower()
    return season_definitions.set_index(["season", "year"])["date"]