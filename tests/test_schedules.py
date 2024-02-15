import pytest, os, datetime
from tradinghours import Market, Currency


LEVEL = os.getenv("API_KEY_LEVEL", "full").strip()

@pytest.mark.parametrize("fin_id, expected", [
    ("US.NYSE", [{'schedule_group': 'Partial', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(6, 30), 'end': datetime.time(9, 30), 'fin_id': 'US.NYSE',
                  'schedule_group_memo': None, 'timezone': 'America/New_York', 'phase_type': 'Pre-Trading Session',
                  'phase_name': 'Pre-Opening Session', 'phase_memo': None, 'days': 'Mon-Fri',
                  'offset_days': 0, 'duration': '10800', 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': None, 'season_end': None, 'end_with_offset': '09:30:00   ',
                  'has_season': False},
                 {'schedule_group': 'Partial', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(9, 30), 'end': datetime.time(13, 0),
                  'fin_id': 'US.NYSE', 'schedule_group_memo': None, 'timezone': 'America/New_York',
                  'phase_type': 'Primary Trading Session', 'phase_name': 'Core Trading Session',
                  'phase_memo': None, 'days': 'Mon-Fri', 'offset_days': 0, 'duration': '12600',
                  'min_start': None, 'max_start': None, 'min_end': None, 'max_end': None,
                  'in_force_end_date': None, 'season_end': None, 'end_with_offset': '13:00:00   ',
                  'has_season': False},
                 {'schedule_group': 'Partial', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(13, 0), 'end': datetime.time(13, 30), 'fin_id': 'US.NYSE',
                  'schedule_group_memo': None, 'timezone': 'America/New_York', 'phase_type': 'Post-Trading Session',
                  'phase_name': 'Crossing Session', 'phase_memo': None, 'days': 'Mon-Fri',
                  'offset_days': 0, 'duration': '1800', 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': None, 'season_end': None, 'end_with_offset': '13:30:00   ',
                  'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(4, 0), 'end': datetime.time(9, 30), 'fin_id': 'US.NYSE',
                  'schedule_group_memo': None, 'timezone': 'America/New_York',
                  'phase_type': 'Pre-Trading Session', 'phase_name': 'Pre-Trading Session', 'phase_memo': None,
                  'days': 'Mon-Fri', 'offset_days': 0, 'duration': '19800', 'min_start': None,
                  'max_start': None, 'min_end': None, 'max_end': None, 'in_force_end_date': None,
                  'season_end': None, 'end_with_offset': '09:30:00   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(6, 30), 'end': datetime.time(9, 30), 'fin_id': 'US.NYSE',
                  'schedule_group_memo': None, 'timezone': 'America/New_York', 'phase_type': 'Pre-Open',
                  'phase_name': 'Pre-Opening Session', 'phase_memo': None, 'days': 'Mon-Fri',
                  'offset_days': 0, 'duration': '10800', 'min_start': None, 'max_start': None, 'min_end': None,
                  'max_end': None, 'in_force_end_date': None, 'season_end': None, 'end_with_offset': '09:30:00   ',
                  'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(9, 30), 'end': datetime.time(9, 30), 'fin_id': 'US.NYSE',
                  'schedule_group_memo': None, 'timezone': 'America/New_York', 'phase_type': 'Call Auction', 'phase_name': 'Core Open Auction', 'phase_memo': None,
                  'days': 'Mon-Fri', 'offset_days': 0, 'duration': '0', 'min_start': None,
                  'max_start': None, 'min_end': None, 'max_end': None, 'in_force_end_date': None, 'season_end': None,
                  'end_with_offset': '09:30:00   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(9, 30), 'end': datetime.time(16, 0), 'fin_id': 'US.NYSE', 'schedule_group_memo': None, 'timezone': 'America/New_York',
                  'phase_type': 'Primary Trading Session', 'phase_name': 'Core Trading Session', 'phase_memo': None,
                  'days': 'Mon-Fri', 'offset_days': 0, 'duration': '23400', 'min_start': None, 'max_start': None,
                  'min_end': None, 'max_end': None, 'in_force_end_date': None, 'season_end': None,
                  'end_with_offset': '16:00:00   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(15, 50), 'end': datetime.time(16, 0), 'fin_id': 'US.NYSE',
                  'schedule_group_memo': None, 'timezone': 'America/New_York', 'phase_type': 'Pre-Close',
                  'phase_name': 'Closing Imbalance Period', 'phase_memo': None, 'days': 'Mon-Fri', 'offset_days': 0,
                  'duration': '600', 'min_start': None, 'max_start': None, 'min_end': None, 'max_end': None,
                  'in_force_end_date': None, 'season_end': None, 'end_with_offset': '16:00:00   ', 'has_season': False},
                 {'schedule_group': 'Regular', 'in_force_start_date': None, 'season_start': None,
                  'start': datetime.time(16, 0), 'end': datetime.time(20, 0), 'fin_id': 'US.NYSE',
                  'schedule_group_memo': None, 'timezone': 'America/New_York', 'phase_type': 'Post-Trading Session',
                  'phase_name': 'Extended Hours', 'phase_memo': None, 'days': 'Mon-Fri', 'offset_days': 0,
                  'duration': '14400', 'min_start': None, 'max_start': None, 'min_end': None, 'max_end': None,
                  'in_force_end_date': None, 'season_end': None, 'end_with_offset': '20:00:00   ',
                  'has_season': False}
                 ]
     )])

def test_list_schedules(fin_id, expected):
    scheds = Market.get(fin_id).list_schedules()
    scheds = [s.to_dict() for s in scheds]
    schedules = []
    for s in scheds:
        # apply custom sorting for easier check if the sorting
        # in .list_schedules is correct
        schedules.append(
            {"schedule_group": s["schedule_group"],
             "in_force_start_date": s["in_force_start_date"],
             "season_start": s["season_start"],
             "start": s["start"],
             "end": s["end"],
             **s}
        )
    assert schedules == expected