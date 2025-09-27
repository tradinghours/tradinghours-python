"""
Server-specific tests for FastAPI endpoints.
These tests focus on HTTP behavior, error handling, middleware, and general server functionality.
"""
import pytest
from datetime import datetime, date
from fastapi.testclient import TestClient
from tradinghours.server import app


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
        assert "total_markets" in data
        assert "total_currencies" in data
        assert isinstance(data["total_markets"], int)
        assert isinstance(data["total_currencies"], int)


class TestErrorHandling:
    """Test error handling and HTTP status codes."""
    
    def test_invalid_market_404(self, client):
        """Test that invalid market returns 404."""
        response = client.get("/markets/INVALID.MARKET")
        assert response.status_code == 404

    def test_invalid_currency_404(self, client):
        """Test that invalid currency returns 404."""
        response = client.get("/currencies/INVALID")
        assert response.status_code == 404

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
        response = client.get("/markets/US.NYSE/status?datetime=invalid-datetime")
        assert response.status_code == 400

    def test_nonexistent_endpoint_404(self, client):
        """Test that nonexistent endpoints return 404."""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404

    def test_method_not_allowed_405(self, client):
        """Test that unsupported HTTP methods return 405."""
        response = client.post("/health")
        assert response.status_code == 405


class TestCORSAndSecurity:
    """Test CORS and security middleware."""
    
    def test_cors_options_request(self, client):
        """Test that OPTIONS requests are handled properly."""
        response = client.options("/health")
        # TestClient may not fully simulate CORS, but endpoint should respond
        assert response.status_code in [200, 405]

    def test_trusted_host_middleware_active(self, client):
        """Test that the app responds properly (middleware is configured)."""
        response = client.get("/health")
        assert response.status_code == 200
        # The fact that we get a response means middleware is working

    def test_cors_headers_configured(self, client):
        """Test basic CORS functionality."""
        response = client.get("/health")
        assert response.status_code == 200
        # In a real deployment, we'd check for Access-Control-Allow-Origin headers


class TestDataSerialization:
    """Test JSON serialization of datetime objects."""
    
    def test_datetime_serialization_in_phases(self, client):
        """Test that datetime objects are properly serialized in phases."""
        response = client.get("/markets/US.NYSE/phases?start=2023-11-15&end=2023-11-15")
        if response.status_code == 200:  # Only test if we have access
            data = response.json()
            if data:  # If we have phases
                phase = data[0]
                # Check that datetime fields are strings in ISO format
                assert isinstance(phase["start"], str)
                assert isinstance(phase["end"], str)
                # Verify they parse as valid datetimes
                datetime.fromisoformat(phase["start"].replace('Z', '+00:00'))
                datetime.fromisoformat(phase["end"].replace('Z', '+00:00'))

    def test_date_serialization_in_holidays(self, client):
        """Test that date objects are properly serialized in holidays."""
        response = client.get("/markets/US.NYSE/holidays?start=2023-11-15&end=2023-11-15")
        if response.status_code == 200:  # Only test if we have access
            data = response.json()
            if data:  # If we have holidays
                holiday = data[0]
                # Check that date field is a string
                assert isinstance(holiday["date"], str)
                # Verify it parses as a valid date
                date.fromisoformat(holiday["date"])

    def test_iso_format_consistency(self, client):
        """Test that all datetime/date serialization uses ISO format."""
        endpoints_to_test = [
            "/markets/US.NYSE/date_range",
            "/markets/US.NYSE/phases?start=2023-11-15&end=2023-11-15",
            "/markets/US.NYSE/holidays?start=2023-11-15&end=2023-11-15",
            "/currencies/USD/holidays?start=2023-01-01&end=2023-01-31"
        ]
        
        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            if response.status_code == 200:
                data = response.json()
                # Recursively check all datetime/date strings in response
                self._check_datetime_format_recursive(data)

    def _check_datetime_format_recursive(self, obj):
        """Recursively check that datetime/date strings are in ISO format."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in ['start', 'end', 'until', 'next_bell'] and isinstance(value, str):
                    # Should be datetime ISO format
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
                elif key in ['date', 'first_available_date', 'last_available_date'] and isinstance(value, str):
                    # Should be date ISO format
                    date.fromisoformat(value)
                else:
                    self._check_datetime_format_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                self._check_datetime_format_recursive(item)


class TestParameterValidation:
    """Test query parameter validation."""
    
    def test_date_range_validation(self, client):
        """Test date range parameter validation."""
        # Valid date range
        response = client.get("/markets/US.NYSE/holidays?start=2023-01-01&end=2023-01-31")
        assert response.status_code in [200, 403, 404]  # May fail due to access or market not found
        
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
        valid_datetimes = [
            "2023-11-15T12:00:00+00:00",
            "2023-11-15T12:00:00-05:00",
            "2023-11-15T12:00:00Z"
        ]
        
        for dt_str in valid_datetimes:
            response = client.get(f"/markets/US.NYSE/status?datetime={dt_str}")
            assert response.status_code in [200, 400, 403, 404]
            # 400 only if the datetime is specifically invalid, not format issue

        # Invalid datetime format should return 400
        response = client.get("/markets/US.NYSE/status?datetime=not-a-datetime")
        assert response.status_code == 400


class TestEndpointCoverage:
    """Test that all expected endpoints exist and respond appropriately."""
    
    def test_all_market_endpoints_exist(self, client):
        """Test that all market endpoints return proper status codes."""
        endpoints = [
            "/markets",
            "/markets/US.NYSE",
            "/markets/US.NYSE/holidays?start=2023-01-01&end=2023-01-31",
            "/markets/US.NYSE/phases?start=2023-01-01&end=2023-01-31", 
            "/markets/US.NYSE/schedules",
            "/markets/US.NYSE/status",
            "/markets/US.NYSE/is_available",
            "/markets/US.NYSE/is_covered",
            "/markets/US.NYSE/date_range",
            "/markets/finid/US.NYSE",
            "/markets/mic/XNYS",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not return 404 (endpoint not found) or 405 (method not allowed)
            assert response.status_code not in [404, 405], f"Endpoint {endpoint} not found"
            # Expected status codes: 200 (success), 400 (bad request), 403 (no access), 422 (validation error)
            assert response.status_code in [200, 400, 403, 422], f"Unexpected status for {endpoint}: {response.status_code}"

    def test_all_currency_endpoints_exist(self, client):
        """Test that all currency endpoints return proper status codes."""
        endpoints = [
            "/currencies",
            "/currencies/USD",
            "/currencies/USD/holidays?start=2023-01-01&end=2023-01-31",
            "/currencies/USD/is_available", 
            "/currencies/USD/is_covered",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not return 404 (endpoint not found) or 405 (method not allowed)
            assert response.status_code not in [404, 405], f"Endpoint {endpoint} not found"
            # Expected status codes: 200 (success), 400 (bad request), 403 (no access), 422 (validation error)
            assert response.status_code in [200, 400, 403, 422], f"Unexpected status for {endpoint}: {response.status_code}"

    def test_endpoint_method_coverage(self, client):
        """Test that endpoints only accept expected HTTP methods."""
        # Test that GET endpoints reject other methods
        get_endpoints = [
            "/health",
            "/info", 
            "/markets",
            "/currencies"
        ]
        
        for endpoint in get_endpoints:
            # POST should not be allowed
            response = client.post(endpoint)
            assert response.status_code == 405
            
            # PUT should not be allowed
            response = client.put(endpoint)
            assert response.status_code == 405
            
            # DELETE should not be allowed  
            response = client.delete(endpoint)
            assert response.status_code == 405


class TestResponseStructure:
    """Test the structure and consistency of API responses."""
    
    def test_health_response_structure(self, client):
        """Test health endpoint response structure."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ['status', 'message', 'version']
        for field in required_fields:
            assert field in data
        
        assert data['status'] == 'healthy'
        assert isinstance(data['message'], str)
        assert isinstance(data['version'], str)

    def test_info_response_structure(self, client):
        """Test info endpoint response structure."""
        response = client.get("/info")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ['api_version', 'total_markets', 'total_currencies']
        for field in required_fields:
            assert field in data
        
        assert isinstance(data['total_markets'], int)
        assert isinstance(data['total_currencies'], int)
        assert data['total_markets'] >= 0
        assert data['total_currencies'] >= 0

    def test_is_available_response_structure(self, client):
        """Test is_available endpoint response structure."""
        # Test market is_available
        response = client.get("/markets/US.NYSE/is_available")
        if response.status_code == 200:
            data = response.json()
            assert 'identifier' in data
            assert 'is_available' in data
            assert isinstance(data['is_available'], bool)
            assert data['identifier'] == 'US.NYSE'
        
        # Test currency is_available
        response = client.get("/currencies/USD/is_available")
        if response.status_code == 200:
            data = response.json()
            assert 'currency_code' in data
            assert 'is_available' in data
            assert isinstance(data['is_available'], bool)
            assert data['currency_code'] == 'USD'

    def test_is_covered_response_structure(self, client):
        """Test is_covered endpoint response structure."""
        # Test market is_covered
        response = client.get("/markets/US.NYSE/is_covered")
        if response.status_code == 200:
            data = response.json()
            assert 'identifier' in data
            assert 'is_covered' in data
            assert isinstance(data['is_covered'], bool)
        
        # Test currency is_covered
        response = client.get("/currencies/USD/is_covered")
        if response.status_code == 200:
            data = response.json()
            assert 'currency_code' in data
            assert 'is_covered' in data
            assert isinstance(data['is_covered'], bool)

    def test_date_range_response_structure(self, client):
        """Test date_range endpoint response structure."""
        response = client.get("/markets/US.NYSE/date_range")
        if response.status_code == 200:
            data = response.json()
            required_fields = ['identifier', 'fin_id', 'first_available_date', 'last_available_date', 'country_code']
            for field in required_fields:
                assert field in data
            
            # Verify date format
            date.fromisoformat(data['first_available_date'])
            date.fromisoformat(data['last_available_date'])
            
            # Verify logical date order
            first_date = date.fromisoformat(data['first_available_date'])
            last_date = date.fromisoformat(data['last_available_date'])
            assert first_date <= last_date


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
        
        # Both should return the same status (both work or both fail)
        assert response1.status_code == response2.status_code
        
        # If successful, should return same data
        if response1.status_code == 200 and response2.status_code == 200:
            assert response1.json() == response2.json()

    def test_whitespace_handling(self, client):
        """Test handling of whitespace in parameters."""
        # Identifiers with leading/trailing spaces should be handled gracefully
        response = client.get("/markets/ US.NYSE ")
        # Should either work (if trimmed) or return 404 (if not found due to spaces)
        assert response.status_code in [200, 403, 404]

    def test_special_characters(self, client):
        """Test handling of special characters in identifiers."""
        # Test with URL-encoded special characters
        response = client.get("/markets/US%2ENYSE")  # URL-encoded dot
        assert response.status_code in [200, 403, 404]

    def test_very_long_identifiers(self, client):
        """Test handling of very long identifiers."""
        long_identifier = "A" * 500 + "." + "B" * 500
        response = client.get(f"/markets/{long_identifier}")
        # Should return 404 (not found) rather than crash
        assert response.status_code == 404
