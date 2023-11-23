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
    """

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


class TestCase004(EdgeCase):
    """

    Test there are correct schedules with schedule coming from the proceeding day, Regular Schedule (overnight)

    """

    def test_case(self):
        fin_id = "US.CME.EQUITY.USINDEX1"
        date = "2023-11-13"
        expected = [
            "Primary Trading Session",
            "Pre-Open",
            "Primary Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected)


class TestCase005(EdgeCase):
    """

    Test there are correct schedules with schedule coming from the proceeding day, Irregular Schedule (overnight)

    """

    def test_case(self):
        fin_id = "US.CME.EQUITY.USINDEX1"
        date = "2023-11-23"
        expected = [
            "Primary Trading Session",
            "Pre-Open",
            "Primary Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected)


class TestCase006(EdgeCase):
    """

    Test there are not schedules coming from the proceeding day when there is a holiday, but normally there would be an overnight schedule

    """

    def test_case(self):
        fin_id = "US.CME.EQUITY.USINDEX1"
        date = "2023-12-25"
        expected = [
            "Pre-Open",
            "Primary Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected)


class TestCase007(EdgeCase):
    """

    Test there are correct schedules on a working Weekend (If Saturday is set
    as Regular in the holidays table, but the regular schedule is normally
    M-F, ignore the day of week.)

    """

    def test_case(self):
        fin_id = "CN.CIBM"
        date = "2020-01-19"
        expected = [
            "Primary Trading Session",
            "Intermission",
            "Primary Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected)


class TestCase008(EdgeCase):
    """
    Test the correct schedule for the day of the week is returned for schedule
    with different hours on different days of the week

    """

    def test_case_thu(self):
        fin_id = "US.CBOE.VIX"
        date = "2020-10-15"
        expected = [
            "Trading-at-Last",
            "Primary Trading Session",
            "Primary Trading Session",
            "Post-Trading Session",
            "Pre-Open",
            "Trading-at-Last",
            "Primary Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected)

    def test_case_fri(self):
        fin_id = "US.CBOE.VIX"
        date = "2020-10-16"
        expected = [
            "Trading-at-Last",
            "Primary Trading Session",
            "Primary Trading Session",
            "Post-Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected)


class TestCase009(EdgeCase):
    """

    Test there are correct schedules on irregular day when the irregular schedule
    does have a schedule for the current day of the week

    """

    def test_case_sun(self):
        fin_id = "US.CME.AGRI.DAIRY1"
        date = "2022-01-16"
        expected = [
            "Pre-Open",
        ]
        self.assertDateSchedule(fin_id, date, expected)

    def test_case_mon(self):
        fin_id = "US.CME.AGRI.DAIRY1"
        date = "2022-01-17"
        expected = [
            "Pre-Open",
            "Primary Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected)

    def test_case_reg_sun(self):
        fin_id = "US.CME.AGRI.DAIRY1"
        date = "2022-01-09"
        expected = [
            "Pre-Open",
            "Primary Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected)

    def test_case_reg_mon(self):
        fin_id = "US.CME.AGRI.DAIRY1"
        date = "2022-01-10"
        expected = [
            "Primary Trading Session",
            "Pre-Open",
            "Primary Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected)
