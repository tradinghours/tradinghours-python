import datetime as dt
from dateutil.parser import parse
import pandas as pd

def calc_concrete_dates(fin_id, start, end, with_holidays=True, _data=None):
    if _data is None:
        raise ValueError("missing data")

    start = dt.datetime.fromisoformat(start)
    end = dt.datetime.fromisoformat(end)

    print(_data.keys())
    schedules = _data["schedules"]
    holidays = _data["holidays"]

    # get all markets schedules in certain order
    print(schedules.columns)
    schedules = schedules[schedules.fin_id == fin_id].sort_values(
        ["start", "duration"], ascending=True
    )
    print(schedules)


    # get all relevant holidays
    print(holidays.columns)
    holidays.date = holidays.date.astype("datetime64[ns]")
    date_match = (holidays.date >= start - dt.timedelta(weeks=1)) & (holidays.date <= end)
    holidays = holidays[(holidays.fin_id == fin_id) & date_match].sort_values("date")
    print(holidays)


    # match holidays with requested dates (making sure schedules with offset_days are included)
    max_offset = schedules.offset_days.max()
    max_offset = int(max_offset) if pd.notna(max_offset) else 0
    dates = pd.date_range(start - dt.timedelta(days=max_offset), end, freq="D").to_series(name="date")
    d_hols = holidays.merge(dates, how='right', left_on="date", right_index=True)
    d_hols = d_hols.drop(columns=["date_x", "date_y"])
    # set non holidays dates to "Regular" schedule group
    d_hols.loc[d_hols.schedule.isna(), "schedule"] = "Regular" # TODO: see about constants like Tradinghours::REGULAR

    # match the schedules to the holidays.
    # Any rows that are NaN after this, have no schedule according to the holiday's schedule_group
    # weekdays/seasons still need to be handled
    full = d_hols.merge(schedules, how="inner", left_on="schedule", right_on="schedule_group")
    print(full.iloc[:, :5].to_string())

    # filter out seasonal
    tz = full.timezone.unique()[0]
    full.date = full.date.dt.tz_localize(tz if pd.notna(tz) else "UTC")
    is_seasonal = full.season_start.notna() | full.season_end.notna()
    seasonal = full.loc[is_seasonal, ["date", "season_start", "season_end"]]
    years = " " + seasonal.date.dt.year.astype("string")
    full["start_date"] = (seasonal.season_start + years).apply(parse)
    full["end_date"] = (seasonal.season_end + years).apply(parse)

    _temp = is_seasonal & (full.start_date > full.end_date)
    in_season = _temp & (full.start_date <= full.date) & (full.end_date >= full.date)
    _temp = is_seasonal & (full.start_date <= full.end_date)
    in_season = in_season | (_temp & (full.start_date >= full.date) & (full.end_date <= full.date))
    full = full[(~is_seasonal) | in_season]

    # filter out in_force
    has_in_force_start = full.in_force_start_date.notna()
    full = full[(~has_in_force_start) | (full.in_force_start_date < full.date)]
    has_in_force_end = full.in_force_end_date.notna()
    full = full[(~has_in_force_end) | (full.in_force_end_date > full.date)]


    return schedules, holidays, d_hols, full



