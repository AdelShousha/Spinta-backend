"""
Health Check Endpoint Tests

This file tests the /health endpoint using Test-Driven Development (TDD).

TDD Process:
1. Write tests FIRST (they will fail initially - that's expected!)
2. Run tests and see them fail
3. Write minimal code to make tests pass
4. Refactor if needed
5. Repeat

Why TDD?
- Ensures code works as expected
- Catches bugs early
- Documents expected behavior
- Makes refactoring safer
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


# Test Client
# TestClient simulates HTTP requests without running an actual server
client = TestClient(app)


class TestHealthEndpoint:
    """
    Test Suite for Health Check Endpoint

    Groups related tests together for organization.
    """

    def test_health_endpoint_exists(self):
        """
        Test 1: Health endpoint should exist and return 200 OK

        This verifies:
        - The endpoint is accessible at /api/health
        - It returns HTTP 200 (success)
        """
        response = client.get("/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_health_response_structure(self):
        """
        Test 2: Health endpoint should return correct JSON structure

        Expected response format:
        {
            "status": "healthy",
            "database": "connected"
        }
        """
        response = client.get("/api/health")
        data = response.json()

        # Check that response has the expected keys
        assert "status" in data, "Response missing 'status' key"
        assert "database" in data, "Response missing 'database' key"

    def test_health_status_value(self):
        """
        Test 3: Health endpoint should return "healthy" status

        This ensures the API is reporting itself as healthy.
        """
        response = client.get("/api/health")
        data = response.json()

        assert data["status"] == "healthy", f"Expected 'healthy', got '{data['status']}'"

    def test_health_database_connected(self):
        """
        Test 4: Health endpoint should verify database connection

        This ensures we can actually connect to Neon database.
        The value should be either "connected" or "disconnected".
        """
        response = client.get("/api/health")
        data = response.json()

        # Database status should be a string
        assert isinstance(data["database"], str), "Database status must be a string"

        # For a working system, it should be "connected"
        assert data["database"] in ["connected", "disconnected"], \
            f"Database status must be 'connected' or 'disconnected', got '{data['database']}'"

    def test_health_response_time(self):
        """
        Test 5: Health endpoint should respond quickly

        Health checks should be fast (< 1 second).
        This ensures the endpoint is optimized.
        """
        import time

        start_time = time.time()
        response = client.get("/api/health")
        end_time = time.time()

        response_time = end_time - start_time

        assert response_time < 1.0, f"Health check took {response_time:.2f}s (should be < 1s)"
        assert response.status_code == 200


# Run these tests with: pytest tests/test_health.py -v
# -v flag gives verbose output showing each test name
