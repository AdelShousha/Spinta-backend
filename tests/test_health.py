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
# when using TestClient it knows how to test the async endpoints using sync function, without the need of async test functions nor the @pytest.mark.asyncio decorator
client = TestClient(app)


class TestHealthEndpoint:
    """
    Test Suite for Health Check Endpoint
    """

    def test_health_check_full_response(self):
        """
        Test 1: Check endpoint status, structure, and values in one call.

        This is the primary "happy path" test. It verifies:
        - The endpoint returns 200 OK.
        - The JSON keys ("status", "database") are correct.
        - The JSON values ("healthy", "connected") are correct.
        """
        response = client.get("/api/health")

        # Test 1: Endpoint exists and is OK
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()

        # Test 2: Response structure (contract)
        assert "status" in data, "Response missing 'status' key"
        assert "database" in data, "Response missing 'database' key"

        # Test 3 & 4: Response values (logic)
        assert data["status"] == "healthy", f"Expected 'healthy', got '{data['status']}'"
        assert data["database"] == "connected", f"Expected 'connected', got '{data['database']}'"


# Run these tests with: pytest tests/test_health.py
