"""
Server-specific tests for FastAPI endpoints.
These tests focus on HTTP behavior, error handling, middleware, and general server functionality.
"""
import pytest
from datetime import datetime, date
from urllib.parse import urlencode
from fastapi.testclient import TestClient
from tradinghours.server import app
from tradinghours import store as st
from tradinghours import exceptions as ex


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestServerHealth:
    """Test server health and info endpoints."""
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "message" in data

    def test_api_info(self, client):
        """Test the API info endpoint."""
        response = client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert "api_version" in data


class TestErrorHandling:
    """Test error handling and HTTP status codes."""
    
    def test_invalid_market_400(self, client):
        """Test that invalid market returns 400."""
        response = client.get("/markets/INVALID.MARKET")
        assert response.status_code == 400

    def test_invalid_currency_400(self, client):
        """Test that invalid currency returns 400."""
        response = client.get("/currencies/INVALID")
        assert response.status_code == 400

    def test_invalid_date_format_422(self, client):
        """Test that invalid date format returns 422."""
        response = client.get("/markets/US.NYSE/holidays?start=invalid-date&end=2023-12-31")
        assert response.status_code == 422  # FastAPI validation error

    def test_missing_required_parameters_422(self, client):
        """Test that missing required parameters return 422."""
        # Missing both start and end dates
        response = client.get("/markets/US.NYSE/holidays")
        assert response.status_code == 422
        
        # Missing end date
        response = client.get("/markets/US.NYSE/holidays?start=2023-01-01")
        assert response.status_code == 422

    def test_invalid_datetime_format_400(self, client):
        """Test that invalid datetime format returns 400."""
        response = client.get("/markets/US.NYSE/status?datetime_utc=invalid-datetime")
        assert response.status_code == 422

    def test_nonexistent_endpoint_404(self, client):
        """Test that nonexistent endpoints return 404."""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404

    def test_method_not_allowed_405(self, client):
        """Test that unsupported HTTP methods return 405."""
        response = client.post("/health")
        assert response.status_code == 405


class TestDataSerialization:
    """Test JSON serialization of datetime objects."""
    
    def test_datetime_serialization_in_phases(self, client):
        """Test that datetime objects are properly serialized in phases."""
        response = client.get("/markets/US.NYSE/phases?start=2023-11-15&end=2023-11-25")
        data = response.json()
        if st.db.access_level == st.AccessLevel.only_holidays:
            assert response.status_code == 400
            return

        phase = data[0]
        # Check that datetime fields are strings in ISO format
        assert isinstance(phase["start"], str)
        assert isinstance(phase["end"], str)
        # Verify they parse as valid datetimes
        datetime.fromisoformat(phase["start"])
        datetime.fromisoformat(phase["end"])

    def test_date_serialization_in_holidays(self, client):
        """Test that date objects are properly serialized in holidays."""
        response = client.get("/markets/US.NYSE/holidays?start=2020-01-01&end=2030-01-01")
        
        data = response.json()
        holiday = data[0]
        # Check that date field is a string
        assert isinstance(holiday["date"], str)
        # Verify it parses as a valid date
        date.fromisoformat(holiday["date"])


class TestParameterValidation:
    """Test query parameter validation."""
    
    def test_date_range_validation(self, client):
        """Test date range parameter validation."""
        # Valid date range
        response = client.get("/markets/US.NYSE/holidays?start=2023-01-01&end=2023-01-31")
        assert response.status_code == 200
        
        # Missing required parameters should return 422
        response = client.get("/markets/US.NYSE/holidays")
        assert response.status_code == 422

        # Invalid date format should return 422
        response = client.get("/markets/US.NYSE/holidays?start=not-a-date&end=2023-01-31")
        assert response.status_code == 422

    def test_boolean_parameters(self, client):
        """Test boolean parameter parsing."""
        # Test follow parameter with different boolean representations
        test_values = ['true', 'false', 'True', 'False', '1', '0']
        
        for value in test_values:
            response = client.get(f"/markets/XBUE?follow={value}")
            assert response.status_code in [200, 403, 404]
            
            response = client.get(f"/markets/finid/AR.BCBA?follow={value}")
            assert response.status_code in [200, 403, 404]

    def test_subset_parameter_validation(self, client):
        """Test subset parameter validation in market listings."""
        # Valid subset patterns
        test_patterns = ['US*', 'US.NYSE*', '*', 'GB*', 'DE*']
        
        for pattern in test_patterns:
            response = client.get(f"/markets?subset={pattern}")
            assert response.status_code in [200, 403]

    def test_datetime_parameter_validation(self, client):
        """Test datetime parameter validation."""
        # Valid ISO datetime formats
        is_restricted = st.db.access_level == st.AccessLevel.only_holidays
        valid_datetimes = [
            "2023-11-15T12:00:00+00:00",
            "2023-11-15T12:00:00Z"
        ]
        for dt_str in valid_datetimes:
            qp = urlencode({"datetime_utc": dt_str})
            response = client.get(f"/markets/US.NYSE/status?{qp}")
            assert response.status_code == 200 if not is_restricted else 400

        # Invalid datetime format should return 422
        qp = urlencode({"datetime_utc": "not-a-datetime"})
        response = client.get(f"/markets/US.NYSE/status?{qp}")
        assert response.status_code == 422 if not is_restricted else 400

        # Invalid timezone offset should return 400
        qp = urlencode({"datetime_utc": "2023-11-15T12:00:00-05:00"})
        response = client.get(f"/markets/US.NYSE/status?{qp}")
        assert response.status_code == 400 if not is_restricted else 400



class TestServerPerformance:
    """Test server performance and response times."""
    
    def test_health_endpoint_fast_response(self, client):
        """Test that health endpoint responds quickly."""
        import time
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        # Health check should be very fast (under 1 second)
        assert (end_time - start_time) < 1.0

    def test_concurrent_requests_handling(self, client):
        """Test that server can handle multiple concurrent requests."""
        import concurrent.futures
        import threading
        
        def make_request():
            return client.get("/health")
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        for response in results:
            assert response.status_code == 200


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_case_sensitivity(self, client):
        """Test case sensitivity in identifiers."""
        # Market identifiers should be case insensitive
        response1 = client.get("/markets/us.nyse")
        response2 = client.get("/markets/US.NYSE")
        
        assert response1.status_code == response2.status_code
        assert response1.json() == response2.json()

    def test_special_characters(self, client):
        """Test handling of special characters in identifiers."""
        # Test with URL-encoded special characters
        response = client.get("/markets/US%2ENYSE")  # URL-encoded dot
        assert response.status_code == 200

    def test_very_long_identifiers(self, client):
        """Test handling of very long identifiers."""
        long_identifier = "A" * 500 + "." + "B" * 500
        response = client.get(f"/markets/{long_identifier}")
        assert response.status_code == 400
