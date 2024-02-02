import pytest
from tradinghours.market import Market

@pytest.mark.parametrize("fin_id, start, end, expected", [
    # Check there are correct schedules on a regularly open day, no holiday
    ("US.NYSE", "2023-11-15", "2023-11-15",
     ['2023-11-15 04:00:00-05:00, 2023-11-15 09:30:00-05:00, Pre-Trading Session',
      '2023-11-15 06:30:00-05:00, 2023-11-15 09:30:00-05:00, Pre-Open',
      '2023-11-15 09:30:00-05:00, 2023-11-15 09:30:00-05:00, Call Auction',
      '2023-11-15 09:30:00-05:00, 2023-11-15 16:00:00-05:00, Primary Trading Session',
      '2023-11-15 15:50:00-05:00, 2023-11-15 16:00:00-05:00, Pre-Close',
      '2023-11-15 16:00:00-05:00, 2023-11-15 20:00:00-05:00, Post-Trading Session']
     ),
    # Check there are not schedules on a closed open day, no holiday
    ("US.NYSE", "2023-11-11", "2023-11-11",
     []
     ),
    # Test there are correct schedules on an irregular schedule
    ("US.NYSE", "2023-11-24", "2023-11-24",
     ['2023-11-24 06:30:00-05:00, 2023-11-24 09:30:00-05:00, Pre-Trading Session',
      '2023-11-24 09:30:00-05:00, 2023-11-24 13:00:00-05:00, Primary Trading Session',
      '2023-11-24 13:00:00-05:00, 2023-11-24 13:30:00-05:00, Post-Trading Session']
     ),
    # Test there are correct schedules with schedule coming from the proceeding day, Regular Schedule (overnight)
    ("US.CME.EQUITY.USINDEX1", "2023-11-13", "2023-11-13",
     ['2023-11-12 17:00:00-06:00, 2023-11-13 16:00:00-06:00, Primary Trading Session',
      '2023-11-13 16:45:00-06:00, 2023-11-13 17:00:00-06:00, Pre-Open',
      '2023-11-13 17:00:00-06:00, 2023-11-14 16:00:00-06:00, Primary Trading Session']
     ),
    # Test there are correct schedules with schedule coming from the proceeding day, Irregular Schedule (overnight)
    ("US.CME.EQUITY.USINDEX1", "2023-11-23", "2023-11-23",
     ['2023-11-22 17:00:00-06:00, 2023-11-23 12:00:00-06:00, Primary Trading Session',
      '2023-11-23 12:00:00-06:00, 2023-11-23 17:00:00-06:00, Pre-Open',
      '2023-11-23 17:00:00-06:00, 2023-11-24 12:15:00-06:00, Primary Trading Session']
     ),
    # Test there are not schedules coming from the proceeding day when there is a holiday, but normally there would be an overnight schedule
    ("US.CME.EQUITY.USINDEX1", "2023-12-25", "2023-12-25",
      ['2023-12-25 16:00:00-06:00, 2023-12-25 17:00:00-06:00, Pre-Open',
       '2023-12-25 17:00:00-06:00, 2023-12-26 16:00:00-06:00, Primary Trading Session']
    ),
    # Test there are correct schedules on a working Weekend (If Saturday is set
    #     as Regular in the holidays table, but the regular schedule is normally
    #     M-F, ignore the day of week.)
    ("CN.CIBM", "2020-01-19", "2020-01-19",
      ['2020-01-19 09:00:00+08:00, 2020-01-19 12:00:00+08:00, Primary Trading Session',
       '2020-01-19 12:00:00+08:00, 2020-01-19 13:30:00+08:00, Intermission',
       '2020-01-19 13:30:00+08:00, 2020-01-19 20:00:00+08:00, Primary Trading Session']
    ),

    # Test the correct schedule for the day of the week is returned for schedule
    # with different hours on different days of the week
    # -- THURSDAY
    ("US.CBOE.VIX", "2020-10-15", "2020-10-15",
      ['2020-10-14 17:00:00-05:00, 2020-10-15 08:30:00-05:00, Primary Trading Session',
       '2020-10-14 17:00:00-05:00, 2020-10-15 15:00:00-05:00, Trading-at-Last',
       '2020-10-15 08:30:00-05:00, 2020-10-15 15:00:00-05:00, Primary Trading Session',
       '2020-10-15 15:00:00-05:00, 2020-10-15 16:00:00-05:00, Post-Trading Session',
       '2020-10-15 16:45:00-05:00, 2020-10-15 17:00:00-05:00, Pre-Open',
       '2020-10-15 17:00:00-05:00, 2020-10-16 08:30:00-05:00, Primary Trading Session',
       '2020-10-15 17:00:00-05:00, 2020-10-16 15:00:00-05:00, Trading-at-Last']
    ),
    # -- FRIDAY
    ("US.CBOE.VIX", "2020-10-16", "2020-10-16",
      ['2020-10-15 17:00:00-05:00, 2020-10-16 08:30:00-05:00, Primary Trading Session',
       '2020-10-15 17:00:00-05:00, 2020-10-16 15:00:00-05:00, Trading-at-Last',
       '2020-10-16 08:30:00-05:00, 2020-10-16 15:00:00-05:00, Primary Trading Session',
       '2020-10-16 15:00:00-05:00, 2020-10-16 16:00:00-05:00, Post-Trading Session']
    ),

    # Test there are correct schedules on irregular day when the irregular schedule
    # does have a schedule for the current day of the week
    # -- SUNDAY
    ("US.CME.AGRI.DAIRY1", "2022-01-16", "2022-01-16",
      ['2022-01-16 16:00:00-06:00, 2022-01-17 17:00:00-06:00, Pre-Open']
    ),
    # -- MONDAY
    ("US.CME.AGRI.DAIRY1", "2022-01-17", "2022-01-17",
      ['2022-01-16 16:00:00-06:00, 2022-01-17 17:00:00-06:00, Pre-Open',
       '2022-01-17 17:00:00-06:00, 2022-01-18 16:00:00-06:00, Primary Trading Session']
    ),
    # -- REGULAR SUNDAY
    ("US.CME.AGRI.DAIRY1", "2022-01-09", "2022-01-09",
      ['2022-01-09 16:00:00-06:00, 2022-01-09 17:00:00-06:00, Pre-Open',
       '2022-01-09 17:00:00-06:00, 2022-01-10 16:00:00-06:00, Primary Trading Session']
    ),
    # -- REGULAR MONDAY
    ("US.CME.AGRI.DAIRY1", "2022-01-10", "2022-01-10",
      ['2022-01-09 17:00:00-06:00, 2022-01-10 16:00:00-06:00, Primary Trading Session',
       '2022-01-10 16:45:00-06:00, 2022-01-10 17:00:00-06:00, Pre-Open',
       '2022-01-10 17:00:00-06:00, 2022-01-11 16:00:00-06:00, Primary Trading Session']
    ),
    # Test Seasonality cases
    # -- SEASON
    ("US.BTEC.ACTIVES.US", "2023-03-09", "2023-03-09",
      ['2023-03-08 18:30:00-05:00, 2023-03-09 17:30:00-05:00, Primary Trading Session',
       '2023-03-09 18:30:00-05:00, 2023-03-10 17:30:00-05:00, Primary Trading Session']
    ),
    # -- OVERNIGHT
    ("US.BTEC.ACTIVES.US", "2023-11-12", "2023-11-12",
      ['2023-11-12 18:30:00-05:00, 2023-11-13 17:30:00-05:00, Primary Trading Session']
    ),
    # Testing holiday with offset
    # -- SINGLE
    ("CN.SGE", "2023-01-02", "2023-01-02",
      []
    ),
    # -- MULTI
    ("CN.SGE", "2023-01-01", "2023-01-03",
      ['2023-01-03 09:00:00+08:00, 2023-01-03 15:30:00+08:00, Primary Trading Session',
       '2023-01-03 15:00:00+08:00, 2023-01-03 15:30:00+08:00, Other',
       '2023-01-03 15:30:00+08:00, 2023-01-03 15:45:00+08:00, Pre-Close',
       '2023-01-03 15:31:00+08:00, 2023-01-03 15:40:00+08:00, Other',
       '2023-01-03 15:40:00+08:00, 2023-01-03 15:40:00+08:00, Other',
       '2023-01-03 19:45:00+08:00, 2023-01-03 20:00:00+08:00, Pre-Open',
       '2023-01-03 19:50:00+08:00, 2023-01-03 19:59:00+08:00, Other',
       '2023-01-03 20:00:00+08:00, 2023-01-04 02:30:00+08:00, Primary Trading Session']
    ),
    # Partial followed by fully closed holiday, including overnight session
    ("CN.SGE", "2024-09-27", "2024-10-04",
      ['2024-09-26 20:00:00+08:00, 2024-09-27 02:30:00+08:00, Primary Trading Session',
       '2024-09-27 09:00:00+08:00, 2024-09-27 15:30:00+08:00, Primary Trading Session',
       '2024-09-27 15:00:00+08:00, 2024-09-27 15:30:00+08:00, Other',
       '2024-09-27 15:30:00+08:00, 2024-09-27 15:45:00+08:00, Pre-Close',
       '2024-09-27 15:31:00+08:00, 2024-09-27 15:40:00+08:00, Other',
       '2024-09-27 15:40:00+08:00, 2024-09-27 15:40:00+08:00, Other',
       '2024-09-27 19:45:00+08:00, 2024-09-27 20:00:00+08:00, Pre-Open',
       '2024-09-27 19:50:00+08:00, 2024-09-27 19:59:00+08:00, Other',
       '2024-09-27 20:00:00+08:00, 2024-09-28 02:30:00+08:00, Primary Trading Session',
       '2024-09-30 09:00:00+08:00, 2024-09-30 15:30:00+08:00, Primary Trading Session',
       '2024-09-30 15:00:00+08:00, 2024-09-30 15:30:00+08:00, Other',
       '2024-09-30 15:30:00+08:00, 2024-09-30 15:45:00+08:00, Pre-Close',
       '2024-09-30 15:31:00+08:00, 2024-09-30 15:40:00+08:00, Other',
       '2024-09-30 15:40:00+08:00, 2024-09-30 15:40:00+08:00, Other']
    ),
    # replaced market transition (2017-04-16)
    # TODO: Should following a replaced market get rid off the replaced data?
    ("AR.BCBA", "2017-04-10", "2017-04-19",
      ['2017-04-17 10:30:00-03:00, 2017-04-17 11:00:00-03:00, Pre-Trading Session',
       '2017-04-17 11:00:00-03:00, 2017-04-17 17:00:00-03:00, Primary Trading Session',
       '2017-04-17 17:05:00-03:00, 2017-04-17 17:15:00-03:00, Post-Trading Session',
       '2017-04-18 10:30:00-03:00, 2017-04-18 11:00:00-03:00, Pre-Trading Session',
       '2017-04-18 11:00:00-03:00, 2017-04-18 17:00:00-03:00, Primary Trading Session',
       '2017-04-18 17:05:00-03:00, 2017-04-18 17:15:00-03:00, Post-Trading Session',
       '2017-04-19 10:30:00-03:00, 2017-04-19 11:00:00-03:00, Pre-Trading Session',
       '2017-04-19 11:00:00-03:00, 2017-04-19 17:00:00-03:00, Primary Trading Session',
       '2017-04-19 17:05:00-03:00, 2017-04-19 17:15:00-03:00, Post-Trading Session']
    ),
    ("AR.BYMA", "2017-04-10", "2017-04-19",
      ['2017-04-17 10:30:00-03:00, 2017-04-17 11:00:00-03:00, Pre-Trading Session',
       '2017-04-17 11:00:00-03:00, 2017-04-17 17:00:00-03:00, Primary Trading Session',
       '2017-04-17 17:05:00-03:00, 2017-04-17 17:15:00-03:00, Post-Trading Session',
       '2017-04-18 10:30:00-03:00, 2017-04-18 11:00:00-03:00, Pre-Trading Session',
       '2017-04-18 11:00:00-03:00, 2017-04-18 17:00:00-03:00, Primary Trading Session',
       '2017-04-18 17:05:00-03:00, 2017-04-18 17:15:00-03:00, Post-Trading Session',
       '2017-04-19 10:30:00-03:00, 2017-04-19 11:00:00-03:00, Pre-Trading Session',
       '2017-04-19 11:00:00-03:00, 2017-04-19 17:00:00-03:00, Primary Trading Session',
       '2017-04-19 17:05:00-03:00, 2017-04-19 17:15:00-03:00, Post-Trading Session']
    ),

])
def test_schedule(fin_id, start, end, expected):
    market = Market.get(fin_id)
    schedules = list(market.generate_schedules(start, end))
    phases = [f"{s.start}, {s.end}, {s.phase_type}" for s in schedules]
    assert phases == expected
