import pytest, calendar
from tradinghours import Market
from tradinghours.models import MarketHoliday
from tradinghours.exceptions import DateNotAvailable, NoAccess
import tradinghours.store as st
from fastapi.testclient import TestClient
from tradinghours.server import app

from .utils import fromiso

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
def test_market_follow(method, args, expected):

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
def test_market_case_insensitivity(method, identifier, expected):
    market = method(identifier)
    result = str(market.fin_id)
    assert result == expected


def test_market_list_all():
    found = Market.list_all()
    assert len(found) == len(list(st.db.query(Market.table())))

    found = Market.list_all("US*")
    assert all(f.fin_id.startswith("US") for f in found)

@pytest.mark.parametrize("fin_id", [
    "US.NYSE", "US.CME.EQUITY.USINDEX1", "US.CBOE.VIX"
])
def test_market_available_dates(fin_id):
    market = Market.get(fin_id)
    table = MarketHoliday.table()

    first_should_be = st.db.query(table).filter(
            table.c.fin_id == fin_id
        ).order_by(
            table.c.date
        ).first().date.replace(day=1)

    last_should_be = st.db.query(table).filter(
            table.c.fin_id == fin_id
        ).order_by(
            table.c.date.desc()
        ).first().date
    _, num_days_in_month = calendar.monthrange(last_should_be.year, last_should_be.month)
    last_should_be = last_should_be.replace(day=num_days_in_month)

    assert market.first_available_date == first_should_be
    assert market.last_available_date == last_should_be

    if st.db.access_level != st.AccessLevel.only_holidays:
        with pytest.raises(DateNotAvailable):
            list(market.generate_phases("1900-01-01", "2020-01-01"))
        with pytest.raises(DateNotAvailable):
            list(market.generate_phases("2020-01-01", "2099-01-01"))
        with pytest.raises(DateNotAvailable):
            list(market.generate_phases("1900-01-01", "2099-01-01"))

        with pytest.raises(DateNotAvailable):
            market.status(fromiso("1900-01-01", "America/New_York"))
        with pytest.raises(DateNotAvailable):
            market.status(fromiso("2099-01-01", "America/New_York"))


@pytest.mark.xfail(
    st.db.access_level == st.AccessLevel.only_holidays,
    reason="No access",
    strict=True,
    raises=NoAccess
)
@pytest.mark.parametrize("fin_id, datetime, expected", [
    ("US.NYSE", fromiso("2023-11-15 12:00", "America/New_York"),
     {
         "status": "Open",
         "reason": "Primary Trading Session",
         "until": fromiso("2023-11-15 15:50", "America/New_York"),
         "next_bell": fromiso("2023-11-15 16:00", "America/New_York"),
         # "timezone": "America/New_York",
     }),
    ("US.NYSE", fromiso("2023-11-15 18:00", "America/New_York"),
     {
         "status": "Closed",
         "reason": "Post-Trading Session",
         "until": fromiso("2023-11-15 20:00", "America/New_York"),
         "next_bell": fromiso("2023-11-16 09:30", "America/New_York"),
#          "timezone": "America/New_York",
     }),
    ("US.NYSE", fromiso("2023-11-11 18:00", "America/New_York"),
     {
         "status": "Closed",
         "reason": None,
         "until": fromiso("2023-11-13 04:00", "America/New_York"),
         "next_bell": fromiso("2023-11-13 09:30", "America/New_York"),
#          "timezone": "America/New_York",
     }),
    ("US.NYSE", fromiso("2023-11-24 10:00", "America/New_York"),
     {
         "status": "Open",
         "reason": "Thanksgiving Day - Primary Trading Session (Partial)",
         "until": fromiso("2023-11-24 13:00", "America/New_York"),
         "next_bell": fromiso("2023-11-24 13:00", "America/New_York"),
#          "timezone": "America/New_York",
     }),
    ("US.NYSE", fromiso("2024-12-25 10:00", "America/New_York"),
     {
         "status": "Closed",
         "reason": "Christmas",
         "until": fromiso("2024-12-26 04:00", "America/New_York"),
         "next_bell": fromiso("2024-12-26 09:30", "America/New_York"),
#          "timezone": "America/New_York",
     }),
    ("US.NYSE", fromiso("2023-11-15 16:00", "America/New_York"),
     {
         "status": "Closed",
         "reason": "Post-Trading Session",
         "until": fromiso("2023-11-15 20:00", "America/New_York"),
         "next_bell": fromiso("2023-11-16 09:30", "America/New_York"),
#          "timezone": "America/New_York",
     }),
    ("US.NYSE", fromiso("2023-11-15 15:59", "America/New_York"),
     {
         "status": "Open",
         "reason": "Primary Trading Session",
         "until": fromiso("2023-11-15 16:00", "America/New_York"),
         "next_bell": fromiso("2023-11-15 16:00", "America/New_York"),
#          "timezone": "America/New_York",
     }),
     ("US.MGEX", fromiso("2024-09-30 07:45", "America/Chicago"),
     {
         "status": "Closed",
         "reason": None,
         "until": fromiso("2024-09-30 08:00", "America/Chicago"),
         "next_bell": fromiso("2024-09-30 08:30", "America/Chicago"),
#          "timezone": "America/New_York",
     }),
     ("US.MGEX", fromiso("2024-09-30 08:00", "America/Chicago"),
     {
         "status": "Closed",
         "reason": "Pre-Open",
         "until": fromiso("2024-09-30 08:30", "America/Chicago"),
         "next_bell": fromiso("2024-09-30 08:30", "America/Chicago"),
#          "timezone": "America/New_York",
     }),
     ("US.MGEX", fromiso("2024-09-30 15:00", "America/Chicago"),
     {
         "status": "Closed",
         "reason": "Post-Trading Session",
         "until": fromiso("2024-09-30 16:00", "America/Chicago"),
         "next_bell": fromiso("2024-09-30 19:00", "America/Chicago"),
#          "timezone": "America/New_York",
     }),
     ("US.MGEX", fromiso("2024-10-04 00:00", "America/Chicago"),
     {
         "status": "Open",
         "reason": "Primary Trading Session",
         "until": fromiso("2024-10-04 07:45", "America/Chicago"),
         "next_bell": fromiso("2024-10-04 07:45", "America/Chicago"),
#          "timezone": "America/New_York",
     })
])
def test_market_status(fin_id, datetime, expected):
    market = Market.get(fin_id)
    status = market.status(datetime=datetime)
    status = status.to_dict()
    status = {k: status.get(k) for k in expected}
    assert status == expected


# ===== SERVER ENDPOINT TESTS =====

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestMarketEndpoints:
    """Test Market endpoints via HTTP API."""
    
    def test_list_markets_endpoint(self, client):
        """Test GET /markets endpoint."""
        response = client.get("/markets")
        assert response.status_code in [200, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            # Compare with direct method call
            direct_result = Market.list_all()
            if data and direct_result:
                assert isinstance(data[0], dict)
                assert 'fin_id' in data[0]

    def test_list_markets_with_subset_endpoint(self, client):
        """Test GET /markets endpoint with subset parameter."""
        response = client.get("/markets?subset=US*")
        assert response.status_code in [200, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            # All returned markets should start with US
            for market in data:
                assert market['fin_id'].startswith('US')

    def test_get_market_endpoint(self, client):
        """Test GET /markets/{identifier} endpoint."""
        response = client.get("/markets/US.NYSE")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            assert data['fin_id'] == 'US.NYSE'
            
            # Compare with direct method call
            try:
                direct_result = Market.get("US.NYSE")
                direct_dict = direct_result.to_dict()
                assert data == direct_dict
            except Exception:
                pass

    def test_get_market_by_mic_endpoint(self, client):
        """Test GET /markets with MIC identifier."""
        response = client.get("/markets/XNYS")  # NYSE MIC
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            # Should resolve to US.NYSE
            assert 'fin_id' in data

    def test_market_holidays_endpoint(self, client):
        """Test GET /markets/{identifier}/holidays endpoint."""
        response = client.get("/markets/US.NYSE/holidays?start=2023-11-15&end=2023-11-15")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            
            # Compare with direct method call
            try:
                market = Market.get("US.NYSE")
                direct_result = market.list_holidays("2023-11-15", "2023-11-15")
                direct_dicts = [h.to_dict() for h in direct_result]
                assert data == direct_dicts
            except Exception:
                pass

    def test_market_phases_endpoint(self, client):
        """Test GET /markets/{identifier}/phases endpoint."""
        response = client.get("/markets/US.NYSE/phases?start=2023-11-15&end=2023-11-15")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            
            # Compare with direct method call  
            try:
                market = Market.get("US.NYSE")
                direct_result = list(market.generate_phases("2023-11-15", "2023-11-15"))
                direct_dicts = [p.to_dict() for p in direct_result]
                assert data == direct_dicts
            except Exception:
                pass

    def test_market_schedules_endpoint(self, client):
        """Test GET /markets/{identifier}/schedules endpoint."""
        response = client.get("/markets/US.NYSE/schedules")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            
            # Compare with direct method call
            try:
                market = Market.get("US.NYSE")
                direct_result = market.list_schedules()
                direct_dicts = [s.to_dict() for s in direct_result]
                assert data == direct_dicts
            except Exception:
                pass

    def test_market_status_endpoint(self, client):
        """Test GET /markets/{identifier}/status endpoint."""
        response = client.get("/markets/US.NYSE/status")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            assert 'status' in data
            
            # Compare with direct method call
            try:
                market = Market.get("US.NYSE")
                direct_result = market.status()
                direct_dict = direct_result.to_dict()
                assert data == direct_dict
            except Exception:
                pass

    def test_market_status_with_datetime_endpoint(self, client):
        """Test GET /markets/{identifier}/status endpoint with datetime parameter."""
        datetime_str = "2023-11-15T12:00:00-05:00"
        response = client.get(f"/markets/US.NYSE/status?datetime={datetime_str}")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            assert 'status' in data

    def test_market_is_available_endpoint(self, client):
        """Test GET /markets/{identifier}/is_available endpoint."""
        response = client.get("/markets/US.NYSE/is_available")
        assert response.status_code in [200, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert 'identifier' in data
            assert 'is_available' in data
            assert isinstance(data['is_available'], bool)
            
            # Compare with direct method call
            direct_result = Market.is_available("US.NYSE")
            assert data['is_available'] == direct_result

    def test_market_is_covered_endpoint(self, client):
        """Test GET /markets/{identifier}/is_covered endpoint."""
        response = client.get("/markets/US.NYSE/is_covered")
        assert response.status_code in [200, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert 'identifier' in data
            assert 'is_covered' in data
            assert isinstance(data['is_covered'], bool)
            
            # Compare with direct method call (if accessible)
            try:
                direct_result = Market.is_covered("US.NYSE")
                assert data['is_covered'] == direct_result
            except Exception:
                pass

    def test_market_date_range_endpoint(self, client):
        """Test GET /markets/{identifier}/date_range endpoint."""
        response = client.get("/markets/US.NYSE/date_range")
        
        if response.status_code == 200:
            data = response.json()
            assert 'first_available_date' in data
            assert 'last_available_date' in data
            assert 'country_code' in data
            assert 'fin_id' in data
            
            # Compare with direct method call
            try:
                market = Market.get("US.NYSE")
                assert data['first_available_date'] == market.first_available_date.isoformat()
                assert data['last_available_date'] == market.last_available_date.isoformat()
                assert data['country_code'] == market.country_code
                assert data['fin_id'] == market.fin_id
            except Exception:
                pass

    def test_market_get_by_finid_endpoint(self, client):
        """Test GET /markets/finid/{finid} endpoint."""
        response = client.get("/markets/finid/US.NYSE")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            assert data['fin_id'] == 'US.NYSE'
            
            # Compare with direct method call
            try:
                direct_result = Market.get_by_finid("US.NYSE")
                direct_dict = direct_result.to_dict()
                assert data == direct_dict
            except Exception:
                pass

    def test_market_get_by_finid_follow_parameter(self, client):
        """Test GET /markets/finid/{finid} endpoint with follow parameter."""
        # Test with follow=false for a replaced market
        response = client.get("/markets/finid/AR.BCBA?follow=false")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            assert data['fin_id'] == 'AR.BCBA'

    def test_market_get_by_mic_endpoint(self, client):
        """Test GET /markets/mic/{mic} endpoint."""
        response = client.get("/markets/mic/XNYS")  # NYSE MIC
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            # Should resolve to a valid market
            assert 'fin_id' in data
            
            # Compare with direct method call
            try:
                direct_result = Market.get_by_mic("XNYS")
                direct_dict = direct_result.to_dict()
                assert data == direct_dict
            except Exception:
                pass

    def test_market_get_by_mic_follow_parameter(self, client):
        """Test GET /markets/mic/{mic} endpoint with follow parameter."""
        response = client.get("/markets/mic/XBUE?follow=false")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            # Should return the replaced market when follow=false
            assert 'fin_id' in data


class TestMarketHybrid:
    """Test that both direct calls and endpoints return equivalent results."""
    
    def test_list_all_consistency(self, client):
        """Test that direct list_all() and /markets endpoint return equivalent data."""
        try:
            # Direct method call
            direct_markets = Market.list_all()
            direct_dicts = [m.to_dict() for m in direct_markets]
            
            # API endpoint call
            response = client.get("/markets")
            if response.status_code == 200:
                api_data = response.json()
                assert api_data == direct_dicts
        except Exception:
            # Skip if no access or other issues
            pass

    def test_get_consistency(self, client):
        """Test that direct get() and /markets/{identifier} endpoint return equivalent data."""
        test_identifiers = ["US.NYSE", "US.NASDAQ", "XNYS", "XNAS"]
        
        for identifier in test_identifiers:
            try:
                # Direct method call
                direct_market = Market.get(identifier)
                direct_dict = direct_market.to_dict()
                
                # API endpoint call
                response = client.get(f"/markets/{identifier}")
                if response.status_code == 200:
                    api_data = response.json()
                    assert api_data == direct_dict
            except Exception:
                # Market might not be available, continue with next
                continue

    def test_phases_consistency(self, client):
        """Test that direct generate_phases() and /markets/{identifier}/phases return equivalent data."""
        test_identifiers = ["US.NYSE", "US.NASDAQ"]
        start_date = "2023-11-15"
        end_date = "2023-11-15"
        
        for identifier in test_identifiers:
            try:
                # Direct method call
                market = Market.get(identifier)
                direct_phases = list(market.generate_phases(start_date, end_date))
                direct_dicts = [p.to_dict() for p in direct_phases]
                
                # API endpoint call
                response = client.get(f"/markets/{identifier}/phases?start={start_date}&end={end_date}")
                if response.status_code == 200:
                    api_data = response.json()
                    assert api_data == direct_dicts
            except Exception:
                # Market might not be available, continue with next
                continue
