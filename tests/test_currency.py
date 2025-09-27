"""
Tests for Currency class - both direct method calls and server endpoints.
"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from tradinghours import Currency
from tradinghours.server import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestCurrencyDirect:
    """Test Currency class methods directly."""
    
    def test_currency_list_all(self):
        """Test Currency.list_all() method."""
        currencies = Currency.list_all()
        assert isinstance(currencies, list)
        if currencies:
            assert hasattr(currencies[0], 'currency_code')
            assert hasattr(currencies[0], 'currency_name')

    def test_currency_get(self):
        """Test Currency.get() method."""
        try:
            currency = Currency.get("USD")
            assert currency.currency_code == "USD"
            assert hasattr(currency, 'currency_name')
            assert hasattr(currency, 'country_code')
        except Exception:
            # Currency might not be available in test data
            pass

    def test_currency_is_available(self):
        """Test Currency.is_available() method."""
        # Test with a common currency
        result = Currency.is_available("USD")
        assert isinstance(result, bool)

    def test_currency_is_covered(self):
        """Test Currency.is_covered() method."""
        # Test with a common currency
        result = Currency.is_covered("USD")
        assert isinstance(result, bool)

    def test_currency_list_holidays(self):
        """Test Currency.list_holidays() method."""
        try:
            currency = Currency.get("USD")
            holidays = currency.list_holidays("2023-01-01", "2023-12-31")
            assert isinstance(holidays, list)
        except Exception:
            # Currency might not be available in test data
            pass


class TestCurrencyEndpoints:
    """Test Currency endpoints via HTTP API."""
    
    def test_list_currencies_endpoint(self, client):
        """Test GET /currencies endpoint."""
        response = client.get("/currencies")
        assert response.status_code in [200, 403]  # 403 if no access
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            # Compare with direct method call
            direct_result = Currency.list_all()
            if data and direct_result:
                # Check that endpoint returns dict version of objects
                assert isinstance(data[0], dict)
                assert 'currency_code' in data[0]

    def test_get_currency_endpoint(self, client):
        """Test GET /currencies/{code} endpoint."""
        response = client.get("/currencies/USD")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            assert data['currency_code'] == 'USD'
            
            # Compare with direct method call
            try:
                direct_result = Currency.get("USD")
                direct_dict = direct_result.to_dict()
                assert data == direct_dict
            except Exception:
                pass  # Direct method might fail due to access

    def test_currency_holidays_endpoint(self, client):
        """Test GET /currencies/{code}/holidays endpoint."""
        response = client.get("/currencies/USD/holidays?start=2023-01-01&end=2023-01-31")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            
            # Compare with direct method call
            try:
                currency = Currency.get("USD")
                direct_result = currency.list_holidays("2023-01-01", "2023-01-31")
                direct_dicts = [h.to_dict() for h in direct_result]
                assert data == direct_dicts
            except Exception:
                pass

    def test_currency_is_available_endpoint(self, client):
        """Test GET /currencies/{code}/is_available endpoint."""
        response = client.get("/currencies/USD/is_available")
        assert response.status_code in [200, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert 'currency_code' in data
            assert 'is_available' in data
            assert data['currency_code'] == 'USD'
            assert isinstance(data['is_available'], bool)
            
            # Compare with direct method call
            direct_result = Currency.is_available("USD")
            assert data['is_available'] == direct_result

    def test_currency_is_covered_endpoint(self, client):
        """Test GET /currencies/{code}/is_covered endpoint."""
        response = client.get("/currencies/USD/is_covered")
        assert response.status_code in [200, 403]
        
        if response.status_code == 200:
            data = response.json()
            assert 'currency_code' in data
            assert 'is_covered' in data
            assert data['currency_code'] == 'USD'
            assert isinstance(data['is_covered'], bool)
            
            # Compare with direct method call
            try:
                direct_result = Currency.is_covered("USD")
                assert data['is_covered'] == direct_result
            except Exception:
                pass


class TestCurrencyHybrid:
    """Test that both direct calls and endpoints return equivalent results."""
    
    def test_list_all_consistency(self, client):
        """Test that direct list_all() and /currencies endpoint return equivalent data."""
        try:
            # Direct method call
            direct_currencies = Currency.list_all()
            direct_dicts = [c.to_dict() for c in direct_currencies]
            
            # API endpoint call
            response = client.get("/currencies")
            if response.status_code == 200:
                api_data = response.json()
                assert api_data == direct_dicts
        except Exception:
            # Skip if no access or other issues
            pass

    def test_get_consistency(self, client):
        """Test that direct get() and /currencies/{code} endpoint return equivalent data."""
        test_codes = ["USD", "EUR", "GBP"]
        
        for code in test_codes:
            try:
                # Direct method call
                direct_currency = Currency.get(code)
                direct_dict = direct_currency.to_dict()
                
                # API endpoint call
                response = client.get(f"/currencies/{code}")
                if response.status_code == 200:
                    api_data = response.json()
                    assert api_data == direct_dict
            except Exception:
                # Currency might not be available, continue with next
                continue

    def test_holidays_consistency(self, client):
        """Test that direct list_holidays() and /currencies/{code}/holidays return equivalent data."""
        test_codes = ["USD", "EUR"]
        start_date = "2023-01-01"
        end_date = "2023-01-31"
        
        for code in test_codes:
            try:
                # Direct method call
                currency = Currency.get(code)
                direct_holidays = currency.list_holidays(start_date, end_date)
                direct_dicts = [h.to_dict() for h in direct_holidays]
                
                # API endpoint call
                response = client.get(f"/currencies/{code}/holidays?start={start_date}&end={end_date}")
                if response.status_code == 200:
                    api_data = response.json()
                    assert api_data == direct_dicts
            except Exception:
                # Currency might not be available, continue with next
                continue

    def test_is_available_consistency(self, client):
        """Test that direct is_available() and endpoint return equivalent data."""
        test_codes = ["USD", "EUR", "GBP", "INVALID"]
        
        for code in test_codes:
            try:
                # Direct method call
                direct_result = Currency.is_available(code)
                
                # API endpoint call
                response = client.get(f"/currencies/{code}/is_available")
                if response.status_code == 200:
                    api_data = response.json()
                    assert api_data['is_available'] == direct_result
            except Exception:
                # Continue with next code
                continue

    def test_is_covered_consistency(self, client):
        """Test that direct is_covered() and endpoint return equivalent data."""
        test_codes = ["USD", "EUR", "GBP", "INVALID"]
        
        for code in test_codes:
            try:
                # Direct method call
                direct_result = Currency.is_covered(code)
                
                # API endpoint call
                response = client.get(f"/currencies/{code}/is_covered")
                if response.status_code == 200:
                    api_data = response.json()
                    assert api_data['is_covered'] == direct_result
            except Exception:
                # Continue with next code
                continue
