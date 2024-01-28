import unittest

from tradinghours.market import Market


class EdgeCase(unittest.TestCase):
    def setUp(self):
        self.market = None

    def assertRangeSchedule(self, fin_id, start, end, expected):
        market = Market.get(fin_id)
        schedules = list(market.generate_schedules(start, end))
        phases = map(lambda s: s.phase_type, schedules)
        result = list(phases)
        self.assertEqual(result, expected)

    def assertDateSchedule(self, fin_id, date, expected):
        self.assertRangeSchedule(fin_id, date, date, expected)

    def assertRangeTimestamps(self, fin_id, start, end, expected):
        market = Market.get(fin_id)
        schedules = list(market.generate_schedules(start, end))
        phases = map(
            lambda s: (s.start.isoformat()[:19], s.end.isoformat()[:19]), schedules
        )
        result = list(phases)
        self.assertEqual(result, expected)

    def assertDateTimestamps(self, fin_id, date, expected):
        self.assertRangeTimestamps(fin_id, date, date, expected)


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
        expected_phases = [
            "Primary Trading Session",
            "Pre-Open",
            "Primary Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected_phases)
        expected_timestamps = [
            ("2023-11-12T17:00:00", "2023-11-13T16:00:00"),
            ("2023-11-13T16:45:00", "2023-11-13T17:00:00"),
            ("2023-11-13T17:00:00", "2023-11-14T16:00:00"),
        ]
        self.assertDateTimestamps(fin_id, date, expected_timestamps)


class TestCase005(EdgeCase):
    """

    Test there are correct schedules with schedule coming from the proceeding day, Irregular Schedule (overnight)

    """

    def test_case(self):
        fin_id = "US.CME.EQUITY.USINDEX1"
        date = "2023-11-23"
        expected_phases = [
            "Primary Trading Session",
            "Pre-Open",
            "Primary Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected_phases)
        expected_timestamps = [
            ("2023-11-22T17:00:00", "2023-11-23T12:00:00"),
            ("2023-11-23T12:00:00", "2023-11-23T17:00:00"),
            ("2023-11-23T17:00:00", "2023-11-24T12:15:00"),
        ]
        self.assertDateTimestamps(fin_id, date, expected_timestamps)


class TestCase006(EdgeCase):
    """

    Test there are not schedules coming from the proceeding day when there is a holiday, but normally there would be an overnight schedule

    """

    def test_case(self):
        fin_id = "US.CME.EQUITY.USINDEX1"
        date = "2023-12-25"
        expected_phases = [
            "Pre-Open",
            "Primary Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected_phases)
        expected_timestamps = [
            ("2023-12-25T16:00:00", "2023-12-25T17:00:00"),
            ("2023-12-25T17:00:00", "2023-12-26T16:00:00"),
        ]
        self.assertDateTimestamps(fin_id, date, expected_timestamps)


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
        # TODO: review this order
        expected_phases = [
            "Primary Trading Session",
            "Trading-at-Last",
            "Primary Trading Session",
            "Post-Trading Session",
            "Pre-Open",
            "Primary Trading Session",
            "Trading-at-Last",
        ]
        self.assertDateSchedule(fin_id, date, expected_phases)
        expected_timestamps = [
            ("2020-10-14T17:00:00", "2020-10-15T08:30:00"),
            ("2020-10-14T17:00:00", "2020-10-15T15:00:00"),
            ("2020-10-15T08:30:00", "2020-10-15T15:00:00"),
            ("2020-10-15T15:00:00", "2020-10-15T16:00:00"),
            ("2020-10-15T16:45:00", "2020-10-15T17:00:00"),
            ("2020-10-15T17:00:00", "2020-10-16T08:30:00"),
            ("2020-10-15T17:00:00", "2020-10-16T15:00:00"),
        ]
        self.assertDateTimestamps(fin_id, date, expected_timestamps)

    def test_case_fri(self):
        fin_id = "US.CBOE.VIX"
        date = "2020-10-16"
        # TODO: review this order
        expected_phases = [
            "Primary Trading Session",
            "Trading-at-Last",
            "Primary Trading Session",
            "Post-Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected_phases)
        expected_timestamps = [
            ("2020-10-15T17:00:00", "2020-10-16T08:30:00"),
            ("2020-10-15T17:00:00", "2020-10-16T15:00:00"),
            ("2020-10-16T08:30:00", "2020-10-16T15:00:00"),
            ("2020-10-16T15:00:00", "2020-10-16T16:00:00"),
        ]
        self.assertDateTimestamps(fin_id, date, expected_timestamps)


class TestCase009(EdgeCase):
    """

    Test there are correct schedules on irregular day when the irregular schedule
    does have a schedule for the current day of the week

    """

    def test_case_sun(self):
        fin_id = "US.CME.AGRI.DAIRY1"
        date = "2022-01-16"
        expected_phases = [
            "Pre-Open",
        ]
        self.assertDateSchedule(fin_id, date, expected_phases)
        expected_timestamps = [
            ("2022-01-16T16:00:00", "2022-01-17T17:00:00"),
        ]
        self.assertDateTimestamps(fin_id, date, expected_timestamps)

    def test_case_mon(self):
        fin_id = "US.CME.AGRI.DAIRY1"
        date = "2022-01-17"
        expected_phases = [
            "Pre-Open",
            "Primary Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected_phases)
        expected_timestamps = [
            ("2022-01-16T16:00:00", "2022-01-17T17:00:00"),
            ("2022-01-17T17:00:00", "2022-01-18T16:00:00"),
        ]
        self.assertDateTimestamps(fin_id, date, expected_timestamps)

    def test_case_reg_sun(self):
        fin_id = "US.CME.AGRI.DAIRY1"
        date = "2022-01-09"
        expected_phases = [
            "Pre-Open",
            "Primary Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected_phases)
        expected_timestamps = [
            ("2022-01-09T16:00:00", "2022-01-09T17:00:00"),
            ("2022-01-09T17:00:00", "2022-01-10T16:00:00"),
        ]
        self.assertDateTimestamps(fin_id, date, expected_timestamps)

    def test_case_reg_mon(self):
        fin_id = "US.CME.AGRI.DAIRY1"
        date = "2022-01-10"
        expected_phases = [
            "Primary Trading Session",
            "Pre-Open",
            "Primary Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected_phases)
        expected_timestamps = [
            ("2022-01-09T17:00:00", "2022-01-10T16:00:00"),
            ("2022-01-10T16:45:00", "2022-01-10T17:00:00"),
            ("2022-01-10T17:00:00", "2022-01-11T16:00:00"),
        ]
        self.assertDateTimestamps(fin_id, date, expected_timestamps)


class TestCase010(EdgeCase):
    """

    Test Seasonality cases

    """

    def test_case_season(self):
        fin_id = "US.BTEC.ACTIVES.US"
        date = "2023-03-09"
        expected_phases = [
            "Primary Trading Session",
            "Primary Trading Session",
        ]
        self.assertDateSchedule(fin_id, date, expected_phases)
        expected_timestamps = [
            ("2023-03-08T18:30:00", "2023-03-09T17:30:00"),
            ("2023-03-09T18:30:00", "2023-03-10T17:30:00"),
        ]
        self.assertDateTimestamps(fin_id, date, expected_timestamps)

    def test_overnight(self):
        fin_id = "US.BTEC.ACTIVES.US"
        date = "2023-11-12"
        expected = [
            ("2023-11-12T18:30:00", "2023-11-13T17:30:00"),
        ]
        self.assertDateTimestamps(fin_id, date, expected)


class TestCase011(EdgeCase):
    """

    Testing holiday with offset

    """

    def test_case_single(self):
        fin_id = "CN.SGE"
        date = "2023-01-02"
        expected = []
        self.assertDateTimestamps(fin_id, date, expected)

    def test_case_multi(self):
        fin_id = "CN.SGE"
        start_date = "2023-01-01"
        end_date = "2023-01-03"
        expected = [
            ("2023-01-03T09:00:00", "2023-01-03T15:30:00"),
            ("2023-01-03T15:00:00", "2023-01-03T15:30:00"),
            ("2023-01-03T15:30:00", "2023-01-03T15:45:00"),
            ("2023-01-03T15:31:00", "2023-01-03T15:40:00"),
            ("2023-01-03T15:40:00", "2023-01-03T15:40:00"),
            ("2023-01-03T19:45:00", "2023-01-03T20:00:00"),
            ("2023-01-03T19:50:00", "2023-01-03T19:59:00"),
            ("2023-01-03T20:00:00", "2023-01-04T02:30:00"),
        ]
        self.assertRangeTimestamps(fin_id, start_date, end_date, expected)


class TestCase012(EdgeCase):
    """

    Test whether you can follow or not a permanently closed market

    """

    def setUp(self):
        self.mic = "XBUE"
        self.old_finid = "AR.BCBA"
        self.new_finid = "AR.BYMA"

    def test_follow_auto_mic(self):
        market = Market.get(self.mic)
        result = str(market.fin_id)
        expected = self.new_finid
        self.assertEqual(result, expected)

    def test_original_auto_mic(self):
        market = Market.get(self.mic, follow=False)
        result = str(market.fin_id)
        expected = self.old_finid
        self.assertEqual(result, expected)

    def test_follow_auto_finid(self):
        market = Market.get(self.old_finid)
        result = str(market.fin_id)
        expected = self.new_finid
        self.assertEqual(result, expected)

    def test_original_auto_finid(self):
        market = Market.get(self.old_finid, follow=False)
        result = str(market.fin_id)
        expected = self.old_finid
        self.assertEqual(result, expected)

    def test_follow_by_mic(self):
        market = Market.get_by_mic(self.mic)
        result = str(market.fin_id)
        expected = self.new_finid
        self.assertEqual(result, expected)

    def test_original_by_mic(self):
        market = Market.get_by_mic(self.mic, follow=False)
        result = str(market.fin_id)
        expected = self.old_finid
        self.assertEqual(result, expected)

    def test_follow_by_finid(self):
        market = Market.get_by_finid(self.old_finid)
        result = str(market.fin_id)
        expected = self.new_finid
        self.assertEqual(result, expected)

    def test_original_by_finid(self):
        market = Market.get_by_finid(self.old_finid, follow=False)
        result = str(market.fin_id)
        expected = self.old_finid
        self.assertEqual(result, expected)


class TestCase013(EdgeCase):
    """

    Test whether MIC case is ignored

    """

    def test_upper_finid(self):
        market = Market.get_by_finid("AR.BYMA")
        result = str(market.fin_id)
        expected = "AR.BYMA"
        self.assertEqual(result, expected)

    def test_lower_finid(self):
        market = Market.get_by_finid("ar.byma")
        result = str(market.fin_id)
        expected = "AR.BYMA"
        self.assertEqual(result, expected)

    def test_mixed_finid(self):
        market = Market.get_by_finid("aR.ByMa")
        result = str(market.fin_id)
        expected = "AR.BYMA"
        self.assertEqual(result, expected)

    def test_upper_mic(self):
        market = Market.get_by_mic("XBUE")
        result = str(market.fin_id)
        expected = "AR.BYMA"
        self.assertEqual(result, expected)

    def test_lower_mic(self):
        market = Market.get_by_mic("xbue")
        result = str(market.fin_id)
        expected = "AR.BYMA"
        self.assertEqual(result, expected)

    def test_mixed_mic(self):
        market = Market.get_by_mic("xBuE")
        result = str(market.fin_id)
        expected = "AR.BYMA"
        self.assertEqual(result, expected)
