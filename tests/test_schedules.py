import pytest, os, datetime
from pprint import pformat
from tradinghours import Market
from tradinghours.exceptions import NoAccess
import tradinghours.store as st


@pytest.mark.xfail(
 st.db.access_level == st.AccessLevel.only_holidays,
 reason="No access", strict=True, raises=NoAccess
)
@pytest.mark.parametrize("fin_id, expected", [
    ("US.NYSE", [{'schedule_group': 'Partial', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(6, 30), 'end': datetime.time(9, 30), 'fin_id': 'US.NYSE',
                  'schedule_group_memo': None, 'timezone': 'America/New_York', 'phase_type': 'Pre-Trading Session',
                  'phase_name': 'Pre-Opening Session', 'phase_memo': None, 'days': 'Mon-Fri',
                  'offset_days': 0, 'duration': 10800, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': None, 'season_end': None, 'end_with_offset': '09:30:00   ',
                  'has_season': False},
                 {'schedule_group': 'Partial', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(9, 30), 'end': datetime.time(13, 0),
                  'fin_id': 'US.NYSE', 'schedule_group_memo': None, 'timezone': 'America/New_York',
                  'phase_type': 'Primary Trading Session', 'phase_name': 'Core Trading Session',
                  'phase_memo': None, 'days': 'Mon-Fri', 'offset_days': 0, 'duration': 12600,
                  'min_start': None, 'max_start': None, 'min_end': None, 'max_end': None,
                  'in_force_end_date': None, 'season_end': None, 'end_with_offset': '13:00:00   ',
                  'has_season': False},
                 {'schedule_group': 'Partial', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(13, 0), 'end': datetime.time(13, 30), 'fin_id': 'US.NYSE',
                  'schedule_group_memo': None, 'timezone': 'America/New_York', 'phase_type': 'Post-Trading Session',
                  'phase_name': 'Crossing Session', 'phase_memo': None, 'days': 'Mon-Fri',
                  'offset_days': 0, 'duration': 1800, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': None, 'season_end': None, 'end_with_offset': '13:30:00   ',
                  'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(4, 0), 'end': datetime.time(9, 30), 'fin_id': 'US.NYSE',
                  'schedule_group_memo': None, 'timezone': 'America/New_York',
                  'phase_type': 'Pre-Trading Session', 'phase_name': 'Pre-Trading Session', 'phase_memo': None,
                  'days': 'Mon-Fri', 'offset_days': 0, 'duration': 19800, 'min_start': None,
                  'max_start': None, 'min_end': None, 'max_end': None, 'in_force_end_date': None,
                  'season_end': None, 'end_with_offset': '09:30:00   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(6, 30), 'end': datetime.time(9, 30), 'fin_id': 'US.NYSE',
                  'schedule_group_memo': None, 'timezone': 'America/New_York', 'phase_type': 'Pre-Open',
                  'phase_name': 'Pre-Opening Session', 'phase_memo': None, 'days': 'Mon-Fri',
                  'offset_days': 0, 'duration': 10800, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': None, 'season_end': None, 'end_with_offset': '09:30:00   ',
                  'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(9, 30), 'end': datetime.time(9, 30), 'fin_id': 'US.NYSE',
                  'schedule_group_memo': None, 'timezone': 'America/New_York', 'phase_type': 'Call Auction', 'phase_name': 'Core Open Auction', 'phase_memo': None,
                  'days': 'Mon-Fri', 'offset_days': 0, 'duration': 0, 'min_start': None,
                  'max_start': None, 'min_end': None, 'max_end': None, 'in_force_end_date': None, 'season_end': None,
                  'end_with_offset': '09:30:00   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(9, 30), 'end': datetime.time(16, 0), 'fin_id': 'US.NYSE', 'schedule_group_memo': None, 'timezone': 'America/New_York',
                  'phase_type': 'Primary Trading Session', 'phase_name': 'Core Trading Session', 'phase_memo': None,
                  'days': 'Mon-Fri', 'offset_days': 0, 'duration': 23400, 'min_start': None, 'max_start': None,
                  'min_end': None, 'max_end': None, 'in_force_end_date': None, 'season_end': None,
                  'end_with_offset': '16:00:00   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(15, 50), 'end': datetime.time(16, 0), 'fin_id': 'US.NYSE',
                  'schedule_group_memo': None, 'timezone': 'America/New_York', 'phase_type': 'Pre-Close',
                  'phase_name': 'Closing Imbalance Period', 'phase_memo': None, 'days': 'Mon-Fri', 'offset_days': 0,
                  'duration': 600, 'min_start': None, 'max_start': None, 'min_end': None, 'max_end': None,
                  'in_force_end_date': None, 'season_end': None, 'end_with_offset': '16:00:00   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(16, 0), 'end': datetime.time(20, 0), 'fin_id': 'US.NYSE',
                  'schedule_group_memo': None, 'timezone': 'America/New_York', 'phase_type': 'Post-Trading Session',
                  'phase_name': 'Extended Hours', 'phase_memo': None, 'days': 'Mon-Fri', 'offset_days': 0,
                  'duration': 14400, 'min_start': None, 'max_start': None, 'min_end': None, 'max_end': None,
                  'in_force_end_date': None, 'season_end': None, 'end_with_offset': '20:00:00   ',
                  'has_season': False}
                 ]
     ),
    ("AE.ADX", [
                 {'schedule_group': 'Regular', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(9, 30), 'end': datetime.time(10, 0), 'fin_id': 'AE.ADX',
                  'schedule_group_memo': None, 'timezone': 'Asia/Dubai', 'phase_type': 'Pre-Open',
                  'phase_name': 'Pre-open Session', 'phase_memo': None, 'days': 'Sun-Thu',
                  'offset_days': 0, 'duration': 1800, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': datetime.date(2021, 3, 3), 'season_end': None,
                  'end_with_offset': '10:00:00   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(10, 0), 'end': datetime.time(13, 50), 'fin_id': 'AE.ADX',
                  'schedule_group_memo': None, 'timezone': 'Asia/Dubai', 'phase_type': 'Primary Trading Session',
                  'phase_name': 'Continuous Trading Session', 'phase_memo': None, 'days': 'Sun-Thu',
                  'offset_days': 0, 'duration': 13800, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': datetime.date(2021, 3, 3), 'season_end': None,
                  'end_with_offset': '13:50:00   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(13, 50), 'end': datetime.time(13, 55), 'fin_id': 'AE.ADX',
                  'schedule_group_memo': None, 'timezone': 'Asia/Dubai', 'phase_type': 'Pre-Close',
                  'phase_name': 'Pre-Closing Session', 'phase_memo': None, 'days': 'Sun-Thu',
                  'offset_days': 0, 'duration': 300, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': datetime.date(2021, 3, 3), 'season_end': None,
                  'end_with_offset': '13:55:00   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': datetime.date(2021, 3, 4), 'season_start': None,
                  'start': datetime.time(9, 30), 'end': datetime.time(10, 0), 'fin_id': 'AE.ADX',
                  'schedule_group_memo': None, 'timezone': 'Asia/Dubai', 'phase_type': 'Pre-Open',
                  'phase_name': 'Pre-open Session', 'phase_memo': None, 'days': 'Sun-Thu',
                  'offset_days': 0, 'duration': 1800, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': datetime.date(2021, 10, 2), 'season_end': None,
                  'end_with_offset': '10:00:00   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': datetime.date(2021, 3, 4), 'season_start': None,
                  'start': datetime.time(10, 0), 'end': datetime.time(13, 50), 'fin_id': 'AE.ADX',
                  'schedule_group_memo': None, 'timezone': 'Asia/Dubai', 'phase_type': 'Primary Trading Session',
                  'phase_name': 'Continuous Trading Session', 'phase_memo': None, 'days': 'Sun-Thu',
                  'offset_days': 0, 'duration': 13800, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': datetime.date(2021, 10, 2), 'season_end': None,
                  'end_with_offset': '13:50:00   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': datetime.date(2021, 3, 4), 'season_start': None,
                  'start': datetime.time(13, 50), 'end': datetime.time(13, 55), 'fin_id': 'AE.ADX',
                  'schedule_group_memo': None, 'timezone': 'Asia/Dubai', 'phase_type': 'Pre-Close',
                  'phase_name': 'Pre-Closing Session', 'phase_memo': None, 'days': 'Sun-Thu',
                  'offset_days': 0, 'duration': 300, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': datetime.date(2021, 10, 2), 'season_end': None,
                  'end_with_offset': '13:55:00   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': datetime.date(2021, 3, 4), 'season_start': None,
                  'start': datetime.time(13, 55), 'end': datetime.time(14, 0), 'fin_id': 'AE.ADX',
                  'schedule_group_memo': None, 'timezone': 'Asia/Dubai', 'phase_type': 'Trading-at-Last',
                  'phase_name': 'Trade At Last Session', 'phase_memo': None, 'days': 'Sun-Thu',
                  'offset_days': 0, 'duration': 300, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': datetime.date(2021, 10, 2), 'season_end': None,
                  'end_with_offset': '14:00:00   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': datetime.date(2021, 10, 3), 'season_start': None,
                  'start': datetime.time(9, 30), 'end': datetime.time(9, 59, 59), 'fin_id': 'AE.ADX',
                  'schedule_group_memo': None, 'timezone': 'Asia/Dubai', 'phase_type': 'Pre-Open',
                  'phase_name': 'Pre-open Session', 'phase_memo': None, 'days': 'Sun-Thu',
                  'offset_days': 0, 'duration': 1799, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': datetime.date(2022, 1, 2), 'season_end': None,
                  'end_with_offset': '09:59:59   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': datetime.date(2021, 10, 3), 'season_start': None,
                  'start': datetime.time(10, 0), 'end': datetime.time(14, 44, 59), 'fin_id': 'AE.ADX',
                  'schedule_group_memo': None, 'timezone': 'Asia/Dubai', 'phase_type': 'Primary Trading Session',
                  'phase_name': 'Continuous Trading Session', 'phase_memo': None, 'days': 'Sun-Thu',
                  'offset_days': 0, 'duration': 17099, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': datetime.date(2022, 1, 2), 'season_end': None,
                  'end_with_offset': '14:44:59   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': datetime.date(2021, 10, 3), 'season_start': None,
                  'start': datetime.time(14, 45), 'end': datetime.time(14, 54, 59), 'fin_id': 'AE.ADX',
                  'schedule_group_memo': None, 'timezone': 'Asia/Dubai', 'phase_type': 'Pre-Close',
                  'phase_name': 'Pre-Closing Session', 'phase_memo': None, 'days': 'Sun-Thu',
                  'offset_days': 0, 'duration': 599, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': datetime.date(2022, 1, 2), 'season_end': None,
                  'end_with_offset': '14:54:59   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': datetime.date(2021, 10, 3), 'season_start': None,
                  'start': datetime.time(14, 55), 'end': datetime.time(15, 0), 'fin_id': 'AE.ADX',
                  'schedule_group_memo': None, 'timezone': 'Asia/Dubai', 'phase_type': 'Trading-at-Last',
                  'phase_name': 'Trade At Last Session', 'phase_memo': None, 'days': 'Sun-Thu',
                  'offset_days': 0, 'duration': 300, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': datetime.date(2022, 1, 2), 'season_end': None,
                  'end_with_offset': '15:00:00   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': datetime.date(2022, 1, 3), 'season_start': None,
                  'start': datetime.time(9, 30), 'end': datetime.time(9, 59, 59), 'fin_id': 'AE.ADX',
                  'schedule_group_memo': None, 'timezone': 'Asia/Dubai', 'phase_type': 'Pre-Open',
                  'phase_name': 'Pre-open Session', 'phase_memo': None, 'days': 'Mon-Fri',
                  'offset_days': 0, 'duration': 1799, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': None, 'season_end': None,
                  'end_with_offset': '09:59:59   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': datetime.date(2022, 1, 3), 'season_start': None,
                  'start': datetime.time(10, 0), 'end': datetime.time(14, 44, 59), 'fin_id': 'AE.ADX',
                  'schedule_group_memo': None, 'timezone': 'Asia/Dubai', 'phase_type': 'Primary Trading Session',
                  'phase_name': 'Continuous Trading Session', 'phase_memo': None, 'days': 'Mon-Fri',
                  'offset_days': 0, 'duration': 17099, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': None, 'season_end': None,
                  'end_with_offset': '14:44:59   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': datetime.date(2022, 1, 3), 'season_start': None,
                  'start': datetime.time(14, 45), 'end': datetime.time(14, 54, 59), 'fin_id': 'AE.ADX',
                  'schedule_group_memo': None, 'timezone': 'Asia/Dubai', 'phase_type': 'Pre-Close',
                  'phase_name': 'Pre-Closing Session', 'phase_memo': None, 'days': 'Mon-Fri',
                  'offset_days': 0, 'duration': 599, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': None, 'season_end': None,
                  'end_with_offset': '14:54:59   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': datetime.date(2022, 1, 3), 'season_start': None,
                  'start': datetime.time(14, 55), 'end': datetime.time(15, 0), 'fin_id': 'AE.ADX',
                  'schedule_group_memo': None, 'timezone': 'Asia/Dubai', 'phase_type': 'Trading-at-Last',
                  'phase_name': 'Trade At Last Session', 'phase_memo': None, 'days': 'Mon-Fri',
                  'offset_days': 0, 'duration': 300, 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': None, 'season_end': None,
                  'end_with_offset': '15:00:00   ', 'has_season': False}
                 ]
)
])
def test_list_schedules(fin_id, expected):
    scheds = Market.get(fin_id).list_schedules()
    scheds = [s.to_dict() for s in scheds]

    assert len(scheds) == len(expected)

    

    matched = []
    for sched in scheds:
        equals = 0
        for i, expect in enumerate(expected):
            if i in matched: continue
            
            matches = False
            if sorted(sched.keys()) == sorted(expect.keys()):
                for k in sched:
                    if sched[k] is None and expect[k] is None:
                        continue
                    try:
                        if sched[k].lower() != expect[k].lower():
                            break
                    except:
                        if sched[k] != expect[k]:
                            break
                        
                else:
                    matches = True

            if matches:
                matched.append(i)
                equals += 1


        assert equals == 1


        # # apply custom sorting of dictionaries
        # # for easier check if the sorting in .list_schedules is correct
        # assert sorted(sched.keys()) == sorted(expect.keys())
        # for k in sched:
        #     assert sched[k] == expect[k], f"{k} failed, expected:\n{pformat(expect)}"
        #
