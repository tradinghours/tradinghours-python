import datetime as dt
import pandas as pd

weekday_mapping = {
    "sunday": "6"
}
day_to_idx = {
    "mon": "0", "tue": "1", "wed": "2", "thu": "3",
    "fri": "4", "sat": "5", "sun": "6"
}
idx_to_day = {

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


def get_schedules_holidays(fin_id, start, end, data):
    #- don't filter, sort with extra fin_id layer
    with_holidays = "holidays" in data
    schedules = data["schedules"]
    if isinstance(fin_id, str) and fin_id != "*":
        schedules = schedules[schedules.fin_id == fin_id]
    else:
        schedules = schedules[schedules.fin_id.isin(fin_id)]

    schedules = schedules.sort_values(["fin_id", "start", "duration"], ascending=True)
    if not with_holidays:
        holidays = pd.DataFrame(columns=["fin_id", "date", "schedule"])
        holidays["date"] = holidays.date.astype("datetime64[ns]")
        return schedules, holidays

    holidays = data["holidays"]
    if isinstance(fin_id, str) and fin_id != "*":
        holidays = holidays[holidays.fin_id == fin_id]
    else:
        holidays = holidays[holidays.fin_id.isin(fin_id)]

    date_match = (holidays.date >= start - dt.timedelta(weeks=1)) & (holidays.date <= end)
    holidays = holidays[date_match].sort_values("date")
    return schedules, holidays


def match_schedules_holidays(schedules, holidays, start, end):
    """
    if end is None, it is assumed that start is the `dates` that would otherwise have to be calculated
    """
    ### match holidays with requested dates (making sure schedules with offset_days are included)
    if end is None:
        dates = start
    else:
        max_offset = schedules.offset_days.max()
        max_offset = int(max_offset) if pd.notna(max_offset) else 0
        dates = pd.date_range(start - dt.timedelta(days=max_offset), end, freq="D")
        dates = pd.MultiIndex.from_product([schedules.fin_id.unique(), dates], names=["fin_id", "date"]).to_frame(index=False)

    #- Would need to make sure that holidays are also matched based on fin_id --> MultiIndex with fin_id
    d_hols = dates.merge(holidays, how="left", left_on=["fin_id", "date"], right_on=["fin_id", "date"])
    # set non holidays dates to "Regular" schedule group
    d_hols.loc[d_hols.schedule.isna(), "schedule"] = "Regular" # TODO: see about constants like Tradinghours::REGULAR

    ### match the schedules to the holidays.
    # Any rows that are NaN after this, have no schedule according to the holiday's schedule_group
    return d_hols.merge(schedules, how="inner", left_on=["fin_id", "schedule"], right_on=["fin_id", "schedule_group"])


def get_full_df(fin_id, start, end, data):
    schedules, holidays = get_schedules_holidays(fin_id, start, end, data)
    return match_schedules_holidays(schedules, holidays, start, end)


def get_full_df_w_index(fin_dates, data):
    fin_ids = fin_dates.fin_id.unique()
    start = fin_dates.date.min()
    end = fin_dates.date.max()
    schedules, holidays = get_schedules_holidays(fin_ids, start, end, data)
    # pass fin_dates as start and None as end, to indicate that the dates index is already created
    return match_schedules_holidays(schedules, holidays, fin_dates, None)


def filter_by_season(full, seasondefs):
    # TODO: fix tz conversion for multiple timezones
    tz = full.timezone.unique()
    tz = "UTC" if not len(tz) else tz[0]
    full.date = full.date.dt.tz_localize(tz if pd.notna(tz) else "UTC")
    full["season_start"] = full.season_start.str.lower()
    full["season_end"] = full.season_end.str.lower()
    is_seasonal = full.season_start.notna() | full.season_end.notna()
    if not is_seasonal.any():
        return full

    seasonal = full.loc[is_seasonal, ["date", "season_start", "season_end"]]
    starts = seasondefs.loc[
        pd.MultiIndex.from_arrays([seasonal.season_start, seasonal.date.dt.year], names=["season", "year"])
    ].drop_duplicates()
    ends = seasondefs.loc[
        pd.MultiIndex.from_arrays([seasonal.season_end, seasonal.date.dt.year], names=["season", "year"])
    ].drop_duplicates()
    del seasonal

    full.index = pd.MultiIndex.from_arrays([full.season_start, full.date.dt.year], names=["season", "year"])
    full = full.merge(starts, left_index=True, right_index=True)
    full[["date", "season_start"]] = full[["date_x", "date_y"]]
    del full["date_x"]
    del full["date_y"]
    del starts

    full.index = pd.MultiIndex.from_arrays([full.season_end, full.date.dt.year], names=["season", "year"])
    full = full.merge(ends, left_index=True, right_index=True)
    full[["date", "season_end"]] = full[["date_x", "date_y"]]
    del full["date_x"]
    del full["date_y"]
    del ends

    full.reset_index(inplace=True)
    del full["season"]
    del full["year"]

    # filter by concrete seasons
    is_seasonal = full.season_start.notna() | full.season_end.notna()
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


def set_is_open(full, phases):
    phases = full[["fin_id", "date", "phase_type", "start", "end", "offset_days"]
        ].merge(phases, how="left", left_on="phase_type", right_on="name")
    phases.index = full.index

    # phases = phases.drop(columns=["phase_type", "name"])
    phases["start"] = phases.date + pd.to_timedelta(phases.start)
    phases["end"] = phases.date + pd.to_timedelta(phases.end
                                                   ) + pd.to_timedelta(phases.offset_days.fillna(0), "D")
    phases["duration"] = (phases["end"] - phases["start"]).dt.total_seconds()
    phases["effective_date"] = (phases["end"] - pd.to_timedelta(1, "ms")).dt.normalize()

    # TODO: still seems like there is a bug
    full["is_open"] = (phases.status == "Open") & (phases.date == phases.effective_date)
    full["is_open"] = full.groupby(["fin_id", "date"]).is_open.transform("any")
    return full


def to_dict(full):
    return {}


#####################
# MAIN ENTRY POINTS #
#####################

def calc_concrete_dates(fin_id, start, end, data):
    if start is None and end is None:
        full = get_full_df_w_index(fin_id, data)
    else:
        if isinstance(start, str):
            start = dt.datetime.fromisoformat(start)
        if isinstance(end, str):
            end = dt.datetime.fromisoformat(end)

        full = get_full_df(fin_id, start, end, data)

    full = filter_by_season(full, data["seasondefs"])

    full = filter_by_in_force(full)

    full = filter_by_day_of_week(full)

    full = set_is_open(full, data["phases"])

    # TODO: should keep weekends and fully closed dates?
    return full


def calc_market_weekend_definitions(fin_ids, data):
    now = pd.to_datetime("now").normalize()
    start = now - pd.to_timedelta(now.weekday(), "D")
    end = now + pd.to_timedelta(6 - now.weekday(), "D")
    # with_holidays=False because we want the generic schedule excluding specific holidays
    full = calc_concrete_dates(fin_ids, start, end, {k:v for k,v in data.items() if k!="holidays"})

    df = full[["fin_id", "date", "is_open"]].drop_duplicates()
    df["weekday"] = df.date.dt.weekday

    wkdays = pd.MultiIndex.from_product([df[df.is_open].fin_id.unique(), range(7)], names=["fin_id", "weekday"]).to_frame(index=False)
    missing = wkdays.merge(df[df.is_open], how="left", left_on=["fin_id", "weekday"], right_on=["fin_id", "weekday"])
    # this is essentially the weekend definition
    missing = missing[missing.date.isna()][["fin_id", "weekday"]].groupby("fin_id").weekday

    df = df.merge(missing.min().rename("min"), how="left", left_on="fin_id", right_index=True)
    df = df.merge(missing.max().rename("max"), how="left", left_on="fin_id", right_index=True)
    return df


def get_dynamic_holidays(fin_ids):
    df = calc_market_weekend_definitions(fin_ids)
    df["regularly_open"] = ~((df["min"] <= df.weekday) & (df.weekday <= df["max"]))
    return df[df.is_open != df.regularly_open]

