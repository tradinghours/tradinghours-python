import unittest

from tradinghours.market import Market


class EdgeCase(unittest.TestCase):
    def setUp(self):
        self.market = None

    def assertRangeSchedule(self, fin_id, start, end, expected):
        market = Market.get(fin_id)
        schedules = market.generate_schedules(start, end)
        phases = map(lambda s: s.phase_type, schedules)
        result = list(phases)
        self.assertEqual(result, expected)

    def assertDateSchedule(self, fin_id, date, expected):
        self.assertRangeSchedule(fin_id, date, date, expected)


class TestCase001(EdgeCase):
    """

    Check there are correct schedules on a regularly open day, no holiday

    """

    def test_case(self):
        fin_id = "US.NYSE"
        date = "2023-11-15"
        expected = [
            "Pre-Trading Session",
            "Pre-Open",
            "Call Auction",
            "Primary Trading Session",
            "Pre-Close",
            "Post-Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected)


class TestCase002(EdgeCase):
    """

    Check there are not schedules on a closed open day, no holiday

    """

    def test_case(self):
        fin_id = "US.NYSE"
        date = "2023-11-11"
        expected = []
        self.assertDateSchedule(fin_id, date, expected)


class TestCase003(EdgeCase):
    """ "

    Test there are correct schedules on an irregular schedule


    """

    def test_case(self):
        fin_id = "US.NYSE"
        date = "2023-11-24"
        expected = [
            "Pre-Trading Session",
            "Primary Trading Session",
            "Post-Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected)
