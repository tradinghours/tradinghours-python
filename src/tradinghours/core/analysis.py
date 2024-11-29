import datetime as dt
from dateutil.parser import parse
from pathlib import Path
import pandas as pd
from .utils import read_sqlite_tables_to_dict

# SQL_DATA = Path(r"storage/database/th-data/data.sqlite")
SQL_DATA = Path(r"C:\TradingHours\pipeline\tradinghours-admin\storage\database\th-data\data.sqlite")


_data = read_sqlite_tables_to_dict(
    SQL_DATA,
    tables=["schedules", "holidays", "season_definitions", "phases"]
)

SCHEDULES = _data["schedules"]
HOLIDAYS = _data["holidays"]
HOLIDAYS["date"] = HOLIDAYS.date.astype("datetime64[ns]")
SEASONDEFS = _data["season_definitions"]
SEASONDEFS["season"] = SEASONDEFS.season.str.lower()
SEASONDEFS = SEASONDEFS.set_index(["season", "year"])["date"]


weekday_mapping = {
    "sunday": "6"
}
day_to_idx = {
    "mon": "0", "tue": "1", "wed": "2", "thu": "3",
    "fri": "4", "sat": "5", "sun": "6"
}


def convert_to_dates(seasons, year):
    """
    Always 4 or 6 words:
     "previous day Second Sunday of march"
     -> the first two words are optional
    """
    split = seasons.str.lower().str.split(" ")
    months = split.str[-1] + " " + year
    months = pd.to_datetime(months, format="%B %Y")

    anchor = split.str[-3]
    anchor_offset = split.str[-4]
    ## Handle "Day"
    # first doesn't need to get done since it is set to first by default in pd.to_datetime
    last = (anchor == "day") & (anchor_offset == "last")
    months.loc[last] = months[last] + pd.to_timedelta(months[last].dt.days_in_month, "d") - pd.to_timedelta(1, "d")

    ## Handle Weekday
    anchor = anchor[anchor != "day"].replace(weekday_mapping).astype("int64")
    _months = months.loc[anchor.index]
    days = _months.repeat(_months.dt.days_in_month)
    days += pd.to_timedelta(pd.Series(index=days.index).fillna(1).groupby(level=0).cumsum(), unit="D")
    days = days[days.dt.weekday == anchor.loc[days.index]]
    daysn = days.groupby(level=0).cumcount()

    for i, offset in enumerate(("first", "second", "last")):
        if offset == "last":
            i = daysn.groupby(level=0).max().loc[daysn.index]
        matches = days[(daysn == i) & (anchor_offset.loc[days.index] == offset)]
        months.loc[matches.index] = matches

    ## Handle optional extra shift
    has_extra = split.str.len() == 6
    previous = split.str[0] == "previous"
    months.loc[has_extra & previous] -= pd.to_timedelta(1, "d")
    months.loc[has_extra & (~previous)] += pd.to_timedelta(1, "d")

    return months


def get_schedules_holidays(fin_id, start, end, with_holidays):
    schedules = SCHEDULES[SCHEDULES.fin_id == fin_id].sort_values(
        ["start", "duration"], ascending=True
    )
    if not with_holidays:
        return schedules, pd.DataFrame(columns=HOLIDAYS.columns)

    date_match = (HOLIDAYS.date >= start - dt.timedelta(weeks=1)) & (HOLIDAYS.date <= end)
    holidays = HOLIDAYS[(HOLIDAYS.fin_id == fin_id) & date_match].sort_values("date")
    return schedules, holidays


def match_schedules_holidays(schedules, holidays, start, end):
    ### match holidays with requested dates (making sure schedules with offset_days are included)
    max_offset = schedules.offset_days.max()
    max_offset = int(max_offset) if pd.notna(max_offset) else 0
    dates = pd.date_range(start - dt.timedelta(days=max_offset), end, freq="D").to_series(name="date")

    d_hols = holidays.merge(dates, how='right', left_on="date", right_index=True)
    d_hols = d_hols.drop(columns=["date_x", "date_y"])
    # set non holidays dates to "Regular" schedule group
    d_hols.loc[d_hols.schedule.isna(), "schedule"] = "Regular" # TODO: see about constants like Tradinghours::REGULAR

    ### match the schedules to the holidays.
    # Any rows that are NaN after this, have no schedule according to the holiday's schedule_group
    return d_hols.merge(schedules, how="inner", left_on="schedule", right_on="schedule_group")


def get_full_df(fin_id, start, end, with_holidays):
    schedules, holidays = get_schedules_holidays(fin_id, start, end, with_holidays)
    return match_schedules_holidays(schedules, holidays, start, end)


def filter_by_season(full):
    tz = full.timezone.unique()
    tz = "UTC" if not len(tz) else tz[0]
    full.date = full.date.dt.tz_localize(tz if pd.notna(tz) else "UTC")
    is_seasonal = full.season_start.notna() | full.season_end.notna()
    if not is_seasonal.any():
        return full

    seasonal = full.loc[is_seasonal, ["date", "season_start", "season_end"]]
    seasonal["season_start"] = seasonal.season_start.str.lower()
    seasonal["season_end"] = seasonal.season_end.str.lower()
    starts = SEASONDEFS.loc[
        pd.MultiIndex.from_arrays([seasonal.season_start, seasonal.date.dt.year], names=["season", "year"])
    ].drop_duplicates()
    ends = SEASONDEFS.loc[
        pd.MultiIndex.from_arrays([seasonal.season_end, seasonal.date.dt.year], names=["season", "year"])
    ].drop_duplicates()

    # starts.index = starts.index.droplevel(1)
    # ends.index = ends.index.droplevel(1)
    full.index = pd.MultiIndex.from_arrays([full.index, full.season_start, full.date.dt.year], names=["ix", "season", "year"])
    seasonal.index = pd.MultiIndex.from_arrays([seasonal.season_start, seasonal.date.dt.year], names=["season", "year"])
    season_start = seasonal.merge(starts, left_on=["season", "year"], right_index=True)["date_y"]
    full = full.merge(season_start, left_on=["season", "year"], right_index=True)
    full["season_start"] = full.date_y
    del full["date_y"]
    full = full.droplevel("season")
    full = full.droplevel("year")


    full.index = mix = pd.MultiIndex.from_arrays([full.index, full.season_end, full.date.dt.year], names=["ix", "season", "year"])
    seasonal.index = pd.MultiIndex.from_arrays([seasonal.season_end, seasonal.date.dt.year], names=["season", "year"])
    season_end = seasonal.merge(ends, left_on=["season", "year"], right_index=True)["date_y"]
    # TODO: sometimes level "ix" disappears
    full = full.merge(season_end, left_on=["season", "year"], right_index=True)
    full.index = mix
    full["season_end"] = full.date_y
    del full["date_y"]
    full = full.droplevel("season")
    full = full.droplevel("year")

    del seasonal, starts, ends


    # filter by concrete seasons
    _temp = is_seasonal & (full.season_start < full.season_end)
    in_season = _temp & (full.season_start <= full.date) & (full.season_end >= full.date)
    _temp = is_seasonal & (full.season_start >= full.season_end)
    in_season = in_season | (_temp & (full.season_start <= full.date) | (full.season_end >= full.date))
    return full[(~is_seasonal) | in_season]


def filter_by_in_force(full):
    full = full[full.in_force_start_date.isna() | (full.in_force_start_date < full.date)]
    return full[full.in_force_end_date.isna() | (full.in_force_end_date > full.date)]


def filter_by_day_of_week(full):
    concrete = full.date.dt.weekday
    days = full.days

    days = days.str.lower().str.replace(r'\s+', '', regex=True)
    days = days.str.split(",").explode()
    days.index = pd.MultiIndex.from_arrays([days.index, days.values], names=["ix", "range"])
    days = days.str.split("-").explode()
    days = days.replace(day_to_idx).astype("int64").to_frame("days")

    concrete.index.name = "ix"
    concrete.name = "concrete"
    df = days.merge(concrete, left_index=True, right_index=True)

    grouped = df.groupby(df.index)
    match = (df.days >= df.concrete) & (grouped.days.shift(1) <= df.concrete)
    # extra OR filter with df.days == df.concrete to ensure strings like "mon" get matched
    return full[(match | (df.days == df.concrete)).groupby(level=0).any()]

def set_is_open(full):
    phases = _data["phases"][["name", "status"]]
    phases = full[["date", "phase_type", "start", "end", "offset_days"]
        ].merge(phases, how="left", left_on="phase_type", right_on="name")

    phases = phases.drop(columns=["phase_type", "name"])
    phases["start"] = phases.date + pd.to_timedelta(phases.start)
    phases["end"] = phases.start + pd.to_timedelta(phases.end
                                                   ) + pd.to_timedelta(phases.offset_days.fillna(0), "D")
    phases["duration"] = (phases["end"] - phases["start"]).dt.total_seconds()
    phases["effective_date"] = (phases["end"] - pd.to_timedelta(1, "ms")).dt.normalize()

    # TODO: still seems like there is a bug
    full["is_open"] = (phases.status == "Open") & (phases.date == phases.effective_date)
    return full

def to_dict(full):
    return {}

def calc_concrete_dates(fin_id, start, end, with_holidays=True):
    if isinstance(start, str):
        start = dt.datetime.fromisoformat(start)
    if isinstance(end, str):
        end = dt.datetime.fromisoformat(end)

    full = get_full_df(fin_id, start, end, with_holidays)

    full = filter_by_season(full)

    full = filter_by_in_force(full)

    full = filter_by_day_of_week(full)

    full = set_is_open(full)

    return full



