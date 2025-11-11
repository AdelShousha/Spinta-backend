"""
Authentication Endpoint Tests

Tests for authentication API endpoints.
Each endpoint has one comprehensive test covering success + error scenarios.

Run with: pytest tests/test_auth.py -v
"""

from datetime import date
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.core.security import create_access_token


# We'll create the client per test with database override
# (not globally, since we need to override get_db with test session)


@pytest.fixture
def client(engine):
    """
    Create a test client with database dependency overridden.

    This ensures API endpoints use the test database session
    instead of the real database connection.
    """
    from sqlalchemy.orm import sessionmaker

    # Ensure tables exist
    from app.models.base import Base
    Base.metadata.create_all(bind=engine)

    # Create a session factory bound to the test engine
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        """
        Create a new session for each request.
        This ensures thread-safety for the TestClient.
        """
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Override lifespan to prevent real database connection
    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        # No database connection for tests
        yield

    # Temporarily replace lifespan
    original_router_lifespan = app.router.lifespan_context
    app.router.lifespan_context = test_lifespan

    with TestClient(app) as test_client:
        yield test_client

    # Restore original lifespan
    app.router.lifespan_context = original_router_lifespan

    # Clean up override
    app.dependency_overrides.clear()


class TestCoachRegistration:
    """
    Tests for POST /api/auth/register/coach endpoint.

    Scenarios: Success, duplicate email, validation errors
    """

    def test_coach_registration_complete_flow(self, client):
        """
        Test complete coach registration flow.

        Scenarios:
        - Successful registration with all fields
        - Returns 201 Created
        - Returns user data with club
        - Returns valid JWT token
        - Password is hashed (not returned)
        - Duplicate email returns 409 Conflict
        """
        # Successful registration
        response = client.post(
            "/api/auth/register/coach",
            json={
                "email": "newcoach@example.com",
                "password": "SecurePass123!",
                "full_name": "New Coach",
                "birth_date": "1990-01-15",
                "gender": "Male",
                "club": {
                    "club_name": "Test FC",
                    "country": "United States",
                    "age_group": "U16",
                    "stadium": "Test Stadium",
                    "logo_url": "https://example.com/logo.png"
                }
            }
        )

        # Verify success
        assert response.status_code == 201
        data = response.json()

        # Verify user data
        assert "user" in data
        assert data["user"]["email"] == "newcoach@example.com"
        assert data["user"]["user_type"] == "coach"
        assert data["user"]["full_name"] == "New Coach"
        assert "user_id" in data["user"]

        # Verify club data included
        assert "club" in data["user"]
        assert data["user"]["club"]["club_name"] == "Test FC"
        assert data["user"]["club"]["age_group"] == "U16"
        assert data["user"]["club"]["stadium"] == "Test Stadium"

        # Verify token returned
        assert "token" in data
        assert len(data["token"]) > 0

        # Verify password NOT returned
        assert "password" not in data["user"]
        assert "password_hash" not in data["user"]

        # Test duplicate email
        duplicate_response = client.post(
            "/api/auth/register/coach",
            json={
                "email": "newcoach@example.com",  # Same email
                "password": "DifferentPass456",
                "full_name": "Another Coach",
                "club": {
                    "club_name": "Another FC"
                }
            }
        )

        assert duplicate_response.status_code == 409
        assert "already exists" in duplicate_response.json()["detail"]


class TestVerifyInvite:
    """
    Tests for POST /api/auth/verify-invite endpoint.

    Scenarios: Valid code, invalid code, already used code
    """

    def test_verify_invite_all_scenarios(self, client, sample_incomplete_player, sample_complete_player):
        """
        Test invite code verification.

        Scenarios:
        - Valid unused code returns 200 with player data
        - Invalid code returns 404
        - Already used code returns 409
        """
        # Test valid unused code
        response = client.post(
            "/api/auth/verify-invite",
            json={
                "invite_code": sample_incomplete_player.invite_code
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["valid"] is True
        assert "player_data" in data

        # Verify player data
        player_data = data["player_data"]
        assert player_data["player_id"] == sample_incomplete_player.player_id
        assert player_data["player_name"] == sample_incomplete_player.player_name
        assert player_data["jersey_number"] == sample_incomplete_player.jersey_number
        assert player_data["position"] == sample_incomplete_player.position
        assert "club_name" in player_data

        # Test invalid code
        invalid_response = client.post(
            "/api/auth/verify-invite",
            json={
                "invite_code": "INVALID-9999"
            }
        )

        assert invalid_response.status_code == 404
        assert "Invalid invite code" in invalid_response.json()["detail"]

        # Test already used code
        used_response = client.post(
            "/api/auth/verify-invite",
            json={
                "invite_code": sample_complete_player.invite_code
            }
        )

        assert used_response.status_code == 409
        assert "already been used" in used_response.json()["detail"]


class TestPlayerRegistration:
    """
    Tests for POST /api/auth/register/player endpoint.

    Scenarios: Success, invalid code, duplicate email, already used code
    """

    def test_player_registration_complete_flow(self, client, sample_incomplete_player):
        """
        Test complete player registration flow.

        Scenarios:
        - Successful registration with valid invite code
        - Returns 201 Created
        - Returns user data with player and club info
        - Returns valid JWT token
        - Invalid invite code returns 404
        - Duplicate email returns 409
        - Already used code returns 409
        """
        invite_code = sample_incomplete_player.invite_code

        # Successful registration
        response = client.post(
            "/api/auth/register/player",
            json={
                "invite_code": invite_code,
                "player_name": "Marcus Silva",
                "email": "marcus@example.com",
                "password": "SecurePass123!",
                "birth_date": "2008-03-20",
                "height": 180,
                "profile_image_url": "https://example.com/marcus.jpg"
            }
        )

        # Verify success
        assert response.status_code == 201
        data = response.json()

        # Verify user data
        assert "user" in data
        assert data["user"]["email"] == "marcus@example.com"
        assert data["user"]["user_type"] == "player"
        assert data["user"]["full_name"] == "Marcus Silva"

        # Verify player-specific data
        assert data["user"]["jersey_number"] == sample_incomplete_player.jersey_number
        assert data["user"]["position"] == sample_incomplete_player.position
        assert data["user"]["birth_date"] == "2008-03-20"

        # Verify club data included
        assert "club" in data["user"]
        assert "club_name" in data["user"]["club"]

        # Verify token returned
        assert "token" in data
        assert len(data["token"]) > 0

        # Test invalid invite code
        invalid_response = client.post(
            "/api/auth/register/player",
            json={
                "invite_code": "INVALID-9999",
                "player_name": "Test Player",
                "email": "newplayer@example.com",  # Use unique email
                "password": "SecurePass123!",
                "birth_date": "2008-01-01",
                "height": 170
            }
        )

        assert invalid_response.status_code == 404
        assert "Invalid invite code" in invalid_response.json()["detail"]

        # Test duplicate email
        duplicate_response = client.post(
            "/api/auth/register/player",
            json={
                "invite_code": "ANOTHER-CODE",  # Doesn't matter, email check comes first
                "player_name": "Another Player",
                "email": "marcus@example.com",  # Duplicate email
                "password": "DifferentPass456",
                "birth_date": "2009-01-01",
                "height": 175
            }
        )

        assert duplicate_response.status_code == 409
        assert "already exists" in duplicate_response.json()["detail"]

        # Test already used invite code
        used_response = client.post(
            "/api/auth/register/player",
            json={
                "invite_code": invite_code,  # Same code already used above
                "player_name": "Another Player",
                "email": "another@example.com",
                "password": "SecurePass123!",
                "birth_date": "2009-01-01",
                "height": 175
            }
        )

        assert used_response.status_code == 409
        assert "already been used" in used_response.json()["detail"]


class TestLogin:
    """
    Tests for POST /api/auth/login endpoint.

    Scenarios: Successful login (coach/player), invalid credentials
    """

    def test_login_all_scenarios(self, client, sample_user, sample_player_user):
        """
        Test user login.

        Scenarios:
        - Successful coach login returns 200 with token
        - Successful player login returns 200 with token
        - Invalid email returns 401
        - Invalid password returns 401
        - Both errors use same message (prevent email enumeration)
        """
        # Test successful coach login
        coach_response = client.post(
            "/api/auth/login",
            json={
                "email": sample_user.email,
                "password": "password123"  # Default password from conftest
            }
        )

        assert coach_response.status_code == 200
        coach_data = coach_response.json()

        # Verify user data
        assert "user" in coach_data
        assert coach_data["user"]["email"] == sample_user.email
        assert coach_data["user"]["user_type"] == "coach"
        assert coach_data["user"]["full_name"] == sample_user.full_name

        # Verify token returned
        assert "token" in coach_data
        assert len(coach_data["token"]) > 0

        # Verify minimal data (no club/player for login)
        assert "club" not in coach_data["user"]
        assert "jersey_number" not in coach_data["user"]

        # Test successful player login
        player_response = client.post(
            "/api/auth/login",
            json={
                "email": sample_player_user.email,
                "password": "password123"
            }
        )

        assert player_response.status_code == 200
        player_data = player_response.json()
        assert player_data["user"]["user_type"] == "player"

        # Test invalid email
        invalid_email_response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )

        assert invalid_email_response.status_code == 401
        error_message = invalid_email_response.json()["detail"]
        assert "Invalid email or password" in error_message

        # Test invalid password
        invalid_password_response = client.post(
            "/api/auth/login",
            json={
                "email": sample_user.email,
                "password": "wrongpassword"
            }
        )

        assert invalid_password_response.status_code == 401
        error_message2 = invalid_password_response.json()["detail"]
        assert "Invalid email or password" in error_message2

        # Verify both errors use same message (security best practice)
        assert error_message == error_message2


class TestTokenValidation:
    """
    Integration tests for token usage across endpoints.

    Tests that tokens from registration/login work correctly.
    """

    def test_tokens_are_valid_jwt(self, client, sample_user):
        """
        Test that returned tokens are valid and can be decoded.

        Scenarios:
        - Login returns valid JWT token
        - Token can be decoded successfully
        - Token contains correct user data
        """
        # Login to get token
        response = client.post(
            "/api/auth/login",
            json={
                "email": sample_user.email,
                "password": "password123"
            }
        )

        assert response.status_code == 200
        token = response.json()["token"]

        # Verify token can be decoded
        from app.core.security import decode_access_token
        payload = decode_access_token(token)

        assert payload is not None
        assert payload["user_id"] == sample_user.user_id
        assert payload["email"] == sample_user.email
        assert payload["user_type"] == sample_user.user_type
