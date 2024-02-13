import pytest
from tradinghours.models import Market

# Test whether you can follow or not a permanently closed market
@pytest.mark.parametrize("method, args, expected", [
    (Market.get, ("XBUE",), "AR.BYMA"),
    (Market.get, ("XBUE", False), "AR.BCBA"),
    (Market.get, ("AR.BCBA",), "AR.BYMA"),
    (Market.get, ("AR.BCBA", False), "AR.BCBA"),
    (Market.get_by_mic, ("XBUE",), "AR.BYMA"),
    (Market.get_by_mic, ("XBUE", False), "AR.BCBA"),
    (Market.get_by_finid, ("AR.BCBA",), "AR.BYMA"),
    (Market.get_by_finid, ("AR.BCBA", False), "AR.BCBA"),
])
def test_market_follow(level, method, args, expected):

    market = method(*args)
    result = str(market.fin_id)
    assert result == expected

# Test whether MIC case is ignored
@pytest.mark.parametrize("method, identifier, expected", [
    (Market.get_by_finid, "AR.BYMA", "AR.BYMA"),
    (Market.get_by_finid, "ar.byma", "AR.BYMA"),
    (Market.get_by_finid, "aR.ByMa", "AR.BYMA"),
    (Market.get_by_mic, "XBUE", "AR.BYMA"),
    (Market.get_by_mic, "xbue", "AR.BYMA"),
    (Market.get_by_mic, "xBuE", "AR.BYMA"),
])
def test_market_case_insensitivity(level, method, identifier, expected):
    market = method(identifier)
    result = str(market.fin_id)
    assert result == expected
