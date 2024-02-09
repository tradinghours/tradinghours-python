import pytest
from tradinghours.market import Market
from pprint import pprint

@pytest.mark.parametrize("fin_id, start, end, expected", [
    ("US.NYSE", "2023-11-15", "2023-11-15",
     [{'phase_type': 'Pre-Trading Session',
       'phase_name': 'Pre-Trading Session',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2023-11-15 04:00:00-05:00', 'UTC-05:00'),
       'end': ('2023-11-15 09:30:00-05:00', 'UTC-05:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Pre-Open',
       'phase_name': 'Pre-Opening Session',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2023-11-15 06:30:00-05:00', 'UTC-05:00'),
       'end': ('2023-11-15 09:30:00-05:00', 'UTC-05:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Call Auction',
       'phase_name': 'Core Open Auction',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2023-11-15 09:30:00-05:00', 'UTC-05:00'),
       'end': ('2023-11-15 09:30:00-05:00', 'UTC-05:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Primary Trading Session',
       'phase_name': 'Core Trading Session',
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2023-11-15 09:30:00-05:00', 'UTC-05:00'),
       'end': ('2023-11-15 16:00:00-05:00', 'UTC-05:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Pre-Close',
       'phase_name': 'Closing Imbalance Period',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2023-11-15 15:50:00-05:00', 'UTC-05:00'),
       'end': ('2023-11-15 16:00:00-05:00', 'UTC-05:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Post-Trading Session',
       'phase_name': 'Extended Hours',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2023-11-15 16:00:00-05:00', 'UTC-05:00'),
       'end': ('2023-11-15 20:00:00-05:00', 'UTC-05:00'),
       'has_settlement': False,
       'is_open': False}]
     ),

    ("US.NYSE", "2023-11-11", "2023-11-11",
     []
     ),

    ("US.NYSE", "2023-11-24", "2023-11-24",
     [{'phase_type': 'Pre-Trading Session',
       'phase_name': 'Pre-Opening Session',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2023-11-24 06:30:00-05:00', 'UTC-05:00'),
       'end': ('2023-11-24 09:30:00-05:00', 'UTC-05:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Primary Trading Session',
       'phase_name': 'Core Trading Session',
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2023-11-24 09:30:00-05:00', 'UTC-05:00'),
       'end': ('2023-11-24 13:00:00-05:00', 'UTC-05:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Post-Trading Session',
       'phase_name': 'Crossing Session',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2023-11-24 13:00:00-05:00', 'UTC-05:00'),
       'end': ('2023-11-24 13:30:00-05:00', 'UTC-05:00'),
       'has_settlement': False,
       'is_open': False}]
     ),

    ("US.CME.EQUITY.USINDEX1", "2023-11-13", "2023-11-13",
     [{'phase_type': 'Primary Trading Session',
       'phase_name': None,
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2023-11-12 17:00:00-06:00', 'UTC-06:00'),
       'end': ('2023-11-13 16:00:00-06:00', 'UTC-06:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Pre-Open',
       'phase_name': None,
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2023-11-13 16:45:00-06:00', 'UTC-06:00'),
       'end': ('2023-11-13 17:00:00-06:00', 'UTC-06:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Primary Trading Session',
       'phase_name': None,
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2023-11-13 17:00:00-06:00', 'UTC-06:00'),
       'end': ('2023-11-14 16:00:00-06:00', 'UTC-06:00'),
       'has_settlement': True,
       'is_open': True}]
     ),

    ("US.CME.EQUITY.USINDEX1", "2023-11-23", "2023-11-23",
     [{'phase_type': 'Primary Trading Session',
       'phase_name': None,
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2023-11-22 17:00:00-06:00', 'UTC-06:00'),
       'end': ('2023-11-23 12:00:00-06:00', 'UTC-06:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Pre-Open',
       'phase_name': None,
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2023-11-23 12:00:00-06:00', 'UTC-06:00'),
       'end': ('2023-11-23 17:00:00-06:00', 'UTC-06:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Primary Trading Session',
       'phase_name': None,
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2023-11-23 17:00:00-06:00', 'UTC-06:00'),
       'end': ('2023-11-24 12:15:00-06:00', 'UTC-06:00'),
       'has_settlement': True,
       'is_open': True}]
     ),

    ("US.CME.EQUITY.USINDEX1", "2023-12-25", "2023-12-25",
     [{'phase_type': 'Pre-Open',
       'phase_name': None,
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2023-12-25 16:00:00-06:00', 'UTC-06:00'),
       'end': ('2023-12-25 17:00:00-06:00', 'UTC-06:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Primary Trading Session',
       'phase_name': None,
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2023-12-25 17:00:00-06:00', 'UTC-06:00'),
       'end': ('2023-12-26 16:00:00-06:00', 'UTC-06:00'),
       'has_settlement': True,
       'is_open': True}]
     ),

    ("CN.CIBM", "2020-01-19", "2020-01-19",
     [{'phase_type': 'Primary Trading Session',
       'phase_name': 'First Session',
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2020-01-19 09:00:00+08:00', 'UTC+08:00'),
       'end': ('2020-01-19 12:00:00+08:00', 'UTC+08:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Intermission',
       'phase_name': 'Intermission',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2020-01-19 12:00:00+08:00', 'UTC+08:00'),
       'end': ('2020-01-19 13:30:00+08:00', 'UTC+08:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Primary Trading Session',
       'phase_name': 'Second Session',
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2020-01-19 13:30:00+08:00', 'UTC+08:00'),
       'end': ('2020-01-19 20:00:00+08:00', 'UTC+08:00'),
       'has_settlement': True,
       'is_open': True}]
     ),

    ("US.CBOE.VIX", "2020-10-15", "2020-10-15",
     [{'phase_type': 'Primary Trading Session',
       'phase_name': 'Extended Trading Hours',
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2020-10-14 17:00:00-05:00', 'UTC-05:00'),
       'end': ('2020-10-15 08:30:00-05:00', 'UTC-05:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Trading-at-Last',
       'phase_name': 'Trade at Settlement',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2020-10-14 17:00:00-05:00', 'UTC-05:00'),
       'end': ('2020-10-15 15:00:00-05:00', 'UTC-05:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Primary Trading Session',
       'phase_name': 'Regular Trading Hours',
       'phase_memo': 'Market Order Acceptance Time',
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2020-10-15 08:30:00-05:00', 'UTC-05:00'),
       'end': ('2020-10-15 15:00:00-05:00', 'UTC-05:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Post-Trading Session',
       'phase_name': 'Extended Trading Hours',
       'phase_memo': 'Post Settlement',
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2020-10-15 15:00:00-05:00', 'UTC-05:00'),
       'end': ('2020-10-15 16:00:00-05:00', 'UTC-05:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Pre-Open',
       'phase_name': None,
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2020-10-15 16:45:00-05:00', 'UTC-05:00'),
       'end': ('2020-10-15 17:00:00-05:00', 'UTC-05:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Primary Trading Session',
       'phase_name': 'Extended Trading Hours',
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2020-10-15 17:00:00-05:00', 'UTC-05:00'),
       'end': ('2020-10-16 08:30:00-05:00', 'UTC-05:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Trading-at-Last',
       'phase_name': 'Trade at Settlement',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2020-10-15 17:00:00-05:00', 'UTC-05:00'),
       'end': ('2020-10-16 15:00:00-05:00', 'UTC-05:00'),
       'has_settlement': False,
       'is_open': False}]
     ),

    ("US.CBOE.VIX", "2020-10-16", "2020-10-16",
     [{'phase_type': 'Primary Trading Session',
       'phase_name': 'Extended Trading Hours',
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2020-10-15 17:00:00-05:00', 'UTC-05:00'),
       'end': ('2020-10-16 08:30:00-05:00', 'UTC-05:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Trading-at-Last',
       'phase_name': 'Trade at Settlement',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2020-10-15 17:00:00-05:00', 'UTC-05:00'),
       'end': ('2020-10-16 15:00:00-05:00', 'UTC-05:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Primary Trading Session',
       'phase_name': 'Regular Trading Hours',
       'phase_memo': 'Market Order Acceptance Time',
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2020-10-16 08:30:00-05:00', 'UTC-05:00'),
       'end': ('2020-10-16 15:00:00-05:00', 'UTC-05:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Post-Trading Session',
       'phase_name': 'Extended Trading Hours',
       'phase_memo': 'Post Settlement',
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2020-10-16 15:00:00-05:00', 'UTC-05:00'),
       'end': ('2020-10-16 16:00:00-05:00', 'UTC-05:00'),
       'has_settlement': False,
       'is_open': False}]
     ),

    ("US.CME.AGRI.DAIRY1", "2022-01-16", "2022-01-16",
     [{'phase_type': 'Pre-Open',
       'phase_name': None,
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2022-01-16 16:00:00-06:00', 'UTC-06:00'),
       'end': ('2022-01-17 17:00:00-06:00', 'UTC-06:00'),
       'has_settlement': False,
       'is_open': False}]
     ),

    ("US.CME.AGRI.DAIRY1", "2022-01-17", "2022-01-17",
     [{'phase_type': 'Pre-Open',
       'phase_name': None,
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2022-01-16 16:00:00-06:00', 'UTC-06:00'),
       'end': ('2022-01-17 17:00:00-06:00', 'UTC-06:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Primary Trading Session',
       'phase_name': None,
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2022-01-17 17:00:00-06:00', 'UTC-06:00'),
       'end': ('2022-01-18 16:00:00-06:00', 'UTC-06:00'),
       'has_settlement': True,
       'is_open': True}]
     ),

    ("US.CME.AGRI.DAIRY1", "2022-01-09", "2022-01-09",
     [{'phase_type': 'Pre-Open',
       'phase_name': None,
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2022-01-09 16:00:00-06:00', 'UTC-06:00'),
       'end': ('2022-01-09 17:00:00-06:00', 'UTC-06:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Primary Trading Session',
       'phase_name': None,
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2022-01-09 17:00:00-06:00', 'UTC-06:00'),
       'end': ('2022-01-10 16:00:00-06:00', 'UTC-06:00'),
       'has_settlement': True,
       'is_open': True}]
     ),

    ("US.CME.AGRI.DAIRY1", "2022-01-10", "2022-01-10",
     [{'phase_type': 'Primary Trading Session',
       'phase_name': None,
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2022-01-09 17:00:00-06:00', 'UTC-06:00'),
       'end': ('2022-01-10 16:00:00-06:00', 'UTC-06:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Pre-Open',
       'phase_name': None,
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2022-01-10 16:45:00-06:00', 'UTC-06:00'),
       'end': ('2022-01-10 17:00:00-06:00', 'UTC-06:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Primary Trading Session',
       'phase_name': None,
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2022-01-10 17:00:00-06:00', 'UTC-06:00'),
       'end': ('2022-01-11 16:00:00-06:00', 'UTC-06:00'),
       'has_settlement': True,
       'is_open': True}]
     ),

    ("US.BTEC.ACTIVES.US", "2023-03-09", "2023-03-09",
     [{'phase_type': 'Primary Trading Session',
       'phase_name': None,
       'phase_memo': 'Winter Season',
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2023-03-08 18:30:00-05:00', 'UTC-05:00'),
       'end': ('2023-03-09 17:30:00-05:00', 'UTC-05:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Primary Trading Session',
       'phase_name': None,
       'phase_memo': 'Winter Season',
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2023-03-09 18:30:00-05:00', 'UTC-05:00'),
       'end': ('2023-03-10 17:30:00-05:00', 'UTC-05:00'),
       'has_settlement': True,
       'is_open': True}]
     ),

    ("US.BTEC.ACTIVES.US", "2023-11-12", "2023-11-12",
     [{'phase_type': 'Primary Trading Session',
       'phase_name': None,
       'phase_memo': 'Winter Season',
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2023-11-12 18:30:00-05:00', 'UTC-05:00'),
       'end': ('2023-11-13 17:30:00-05:00', 'UTC-05:00'),
       'has_settlement': True,
       'is_open': True}]
     ),

    ("CN.SGE", "2023-01-02", "2023-01-02",
     []
     ),

    ("CN.SGE", "2023-01-01", "2023-01-03",
     [{'phase_type': 'Primary Trading Session',
       'phase_name': 'Day Trading Session',
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2023-01-03 09:00:00+08:00', 'UTC+08:00'),
       'end': ('2023-01-03 15:30:00+08:00', 'UTC+08:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Other',
       'phase_name': 'Delivery Tender Submission',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2023-01-03 15:00:00+08:00', 'UTC+08:00'),
       'end': ('2023-01-03 15:30:00+08:00', 'UTC+08:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Pre-Close',
       'phase_name': 'Pre Market Close',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2023-01-03 15:30:00+08:00', 'UTC+08:00'),
       'end': ('2023-01-03 15:45:00+08:00', 'UTC+08:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Other',
       'phase_name': 'Equalizer Tender Submission',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2023-01-03 15:31:00+08:00', 'UTC+08:00'),
       'end': ('2023-01-03 15:40:00+08:00', 'UTC+08:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Other',
       'phase_name': 'Deliver Tender Matching',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2023-01-03 15:40:00+08:00', 'UTC+08:00'),
       'end': ('2023-01-03 15:40:00+08:00', 'UTC+08:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Pre-Open',
       'phase_name': 'Market Opening',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2023-01-03 19:45:00+08:00', 'UTC+08:00'),
       'end': ('2023-01-03 20:00:00+08:00', 'UTC+08:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Other',
       'phase_name': 'Order Matching',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2023-01-03 19:50:00+08:00', 'UTC+08:00'),
       'end': ('2023-01-03 19:59:00+08:00', 'UTC+08:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Primary Trading Session',
       'phase_name': 'Night Trading Session',
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2023-01-03 20:00:00+08:00', 'UTC+08:00'),
       'end': ('2023-01-04 02:30:00+08:00', 'UTC+08:00'),
       'has_settlement': True,
       'is_open': True}]
     ),

    ("CN.SGE", "2024-09-27", "2024-10-04",
     [{'phase_type': 'Primary Trading Session',
       'phase_name': 'Night Trading Session',
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2024-09-26 20:00:00+08:00', 'UTC+08:00'),
       'end': ('2024-09-27 02:30:00+08:00', 'UTC+08:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Primary Trading Session',
       'phase_name': 'Day Trading Session',
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2024-09-27 09:00:00+08:00', 'UTC+08:00'),
       'end': ('2024-09-27 15:30:00+08:00', 'UTC+08:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Other',
       'phase_name': 'Delivery Tender Submission',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2024-09-27 15:00:00+08:00', 'UTC+08:00'),
       'end': ('2024-09-27 15:30:00+08:00', 'UTC+08:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Pre-Close',
       'phase_name': 'Pre Market Close',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2024-09-27 15:30:00+08:00', 'UTC+08:00'),
       'end': ('2024-09-27 15:45:00+08:00', 'UTC+08:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Other',
       'phase_name': 'Equalizer Tender Submission',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2024-09-27 15:31:00+08:00', 'UTC+08:00'),
       'end': ('2024-09-27 15:40:00+08:00', 'UTC+08:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Other',
       'phase_name': 'Deliver Tender Matching',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2024-09-27 15:40:00+08:00', 'UTC+08:00'),
       'end': ('2024-09-27 15:40:00+08:00', 'UTC+08:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Pre-Open',
       'phase_name': 'Market Opening',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2024-09-27 19:45:00+08:00', 'UTC+08:00'),
       'end': ('2024-09-27 20:00:00+08:00', 'UTC+08:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Other',
       'phase_name': 'Order Matching',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2024-09-27 19:50:00+08:00', 'UTC+08:00'),
       'end': ('2024-09-27 19:59:00+08:00', 'UTC+08:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Primary Trading Session',
       'phase_name': 'Night Trading Session',
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2024-09-27 20:00:00+08:00', 'UTC+08:00'),
       'end': ('2024-09-28 02:30:00+08:00', 'UTC+08:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Primary Trading Session',
       'phase_name': 'Day Trading Session',
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2024-09-30 09:00:00+08:00', 'UTC+08:00'),
       'end': ('2024-09-30 15:30:00+08:00', 'UTC+08:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Other',
       'phase_name': 'Delivery Tender Submission',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2024-09-30 15:00:00+08:00', 'UTC+08:00'),
       'end': ('2024-09-30 15:30:00+08:00', 'UTC+08:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Pre-Close',
       'phase_name': 'Pre Market Close',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2024-09-30 15:30:00+08:00', 'UTC+08:00'),
       'end': ('2024-09-30 15:45:00+08:00', 'UTC+08:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Other',
       'phase_name': 'Equalizer Tender Submission',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2024-09-30 15:31:00+08:00', 'UTC+08:00'),
       'end': ('2024-09-30 15:40:00+08:00', 'UTC+08:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Other',
       'phase_name': 'Deliver Tender Matching',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2024-09-30 15:40:00+08:00', 'UTC+08:00'),
       'end': ('2024-09-30 15:40:00+08:00', 'UTC+08:00'),
       'has_settlement': False,
       'is_open': False}]
     ),

    ("AR.BCBA", "2017-04-10", "2017-04-19",
     [{'phase_type': 'Pre-Trading Session',
       'phase_name': 'Opening Session',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2017-04-17 10:30:00-03:00', 'UTC-03:00'),
       'end': ('2017-04-17 11:00:00-03:00', 'UTC-03:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Primary Trading Session',
       'phase_name': 'Trading Session',
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2017-04-17 11:00:00-03:00', 'UTC-03:00'),
       'end': ('2017-04-17 17:00:00-03:00', 'UTC-03:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Post-Trading Session',
       'phase_name': 'Extended Hours',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2017-04-17 17:05:00-03:00', 'UTC-03:00'),
       'end': ('2017-04-17 17:15:00-03:00', 'UTC-03:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Pre-Trading Session',
       'phase_name': 'Opening Session',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2017-04-18 10:30:00-03:00', 'UTC-03:00'),
       'end': ('2017-04-18 11:00:00-03:00', 'UTC-03:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Primary Trading Session',
       'phase_name': 'Trading Session',
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2017-04-18 11:00:00-03:00', 'UTC-03:00'),
       'end': ('2017-04-18 17:00:00-03:00', 'UTC-03:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Post-Trading Session',
       'phase_name': 'Extended Hours',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2017-04-18 17:05:00-03:00', 'UTC-03:00'),
       'end': ('2017-04-18 17:15:00-03:00', 'UTC-03:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Pre-Trading Session',
       'phase_name': 'Opening Session',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2017-04-19 10:30:00-03:00', 'UTC-03:00'),
       'end': ('2017-04-19 11:00:00-03:00', 'UTC-03:00'),
       'has_settlement': False,
       'is_open': False},
      {'phase_type': 'Primary Trading Session',
       'phase_name': 'Trading Session',
       'phase_memo': None,
       'status': 'Open',
       'settlement': 'Yes',
       'start': ('2017-04-19 11:00:00-03:00', 'UTC-03:00'),
       'end': ('2017-04-19 17:00:00-03:00', 'UTC-03:00'),
       'has_settlement': True,
       'is_open': True},
      {'phase_type': 'Post-Trading Session',
       'phase_name': 'Extended Hours',
       'phase_memo': None,
       'status': 'Closed',
       'settlement': 'No',
       'start': ('2017-04-19 17:05:00-03:00', 'UTC-03:00'),
       'end': ('2017-04-19 17:15:00-03:00', 'UTC-03:00'),
       'has_settlement': False,
       'is_open': False}]
     ),
])
def test_schedule(level, fin_id, start, end, expected):
    if level == "only_holidays":
        pytest.xfail()

    market = Market.get(fin_id)
    calculated = list(market.generate_schedules(start, end))

    assert len(calculated) == len(expected)
    for calced, exp in zip(calculated, expected):
        calced = calced.to_dict()
        calced["start"] = str(calced["start"]), calced["start"].tzname()
        calced["end"] = str(calced["end"]), calced["end"].tzname()
        
        assert ((calced["has_settlement"] is False and calced["settlement"] == 'No') or
                (calced["has_settlement"] is True and calced["settlement"] == 'Yes'))
        assert ((calced["is_open"] is False and calced["status"] == 'Closed') or
                (calced["is_open"] is True and calced["status"] == 'Open'))
                    
        assert ((exp["has_settlement"] is False and exp["settlement"] == 'No') or
                (exp["has_settlement"] is True and exp["settlement"] == 'Yes'))
        assert ((exp["is_open"] is False and exp["status"] == 'Closed') or
                (exp["is_open"] is True and exp["status"] == 'Open'))
            
        assert str(calced) == str(exp)


# [
#     # Check there are correct schedules on a regularly open day, no holiday
#     ("US.NYSE", "2023-11-15", "2023-11-15",
#     # Check there are not schedules on a closed open day, no holiday
#     ("US.NYSE", "2023-11-11", "2023-11-11",
#     # Test there are correct schedules on an irregular schedule
#     ("US.NYSE", "2023-11-24", "2023-11-24",
#     # Test there are correct schedules with schedule coming from the proceeding day, Regular Schedule (overnight)
#     ("US.CME.EQUITY.USINDEX1", "2023-11-13", "2023-11-13",
#     # Test there are correct schedules with schedule coming from the proceeding day, Irregular Schedule (overnight)
#     ("US.CME.EQUITY.USINDEX1", "2023-11-23", "2023-11-23",
#     # Test there are not schedules coming from the proceeding day when there is a holiday, but normally there would be an overnight schedule
#     ("US.CME.EQUITY.USINDEX1", "2023-12-25", "2023-12-25",
#     # Test there are correct schedules on a working Weekend (If Saturday is set
#     #     as Regular in the holidays table, but the regular schedule is normally
#     #     M-F, ignore the day of week.)
#     ("CN.CIBM", "2020-01-19", "2020-01-19",
#     # Test the correct schedule for the day of the week is returned for schedule
#     # with different hours on different days of the week
#     # -- THURSDAY
#     ("US.CBOE.VIX", "2020-10-15", "2020-10-15",
#     # -- FRIDAY
#     ("US.CBOE.VIX", "2020-10-16", "2020-10-16",
#     # Test there are correct schedules on irregular day when the irregular schedule
#     # does have a schedule for the current day of the week
#     # -- SUNDAY
#     ("US.CME.AGRI.DAIRY1", "2022-01-16", "2022-01-16",
#     # -- MONDAY
#     ("US.CME.AGRI.DAIRY1", "2022-01-17", "2022-01-17",
#     # -- REGULAR SUNDAY
#     ("US.CME.AGRI.DAIRY1", "2022-01-09", "2022-01-09",
#     # -- REGULAR MONDAY
#     ("US.CME.AGRI.DAIRY1", "2022-01-10", "2022-01-10",
#     # Test Seasonality cases
#     # -- SEASON
#     ("US.BTEC.ACTIVES.US", "2023-03-09", "2023-03-09",
#     # -- OVERNIGHT
#     ("US.BTEC.ACTIVES.US", "2023-11-12", "2023-11-12",
#     # Testing holiday with offset
#     # -- SINGLE
#     ("CN.SGE", "2023-01-02", "2023-01-02",
#     # -- MULTI
#     ("CN.SGE", "2023-01-01", "2023-01-03",
#     # Partial followed by fully closed holiday, including overnight session
#     ("CN.SGE", "2024-09-27", "2024-10-04",
#     # replaced market transition (2017-04-16)
#     # TODO: Should following a replaced market get rid off the replaced data?
#     ("AR.BCBA", "2017-04-10", "2017-04-19",
# ]