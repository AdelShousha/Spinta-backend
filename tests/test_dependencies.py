"""
Authentication Dependency Tests

Tests for FastAPI authentication dependencies.
Tests are grouped by dependency function.

Run with: pytest tests/test_dependencies.py -v
"""

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.dependencies import get_current_user, require_coach, require_player
from app.core.security import create_access_token


class TestGetCurrentUser:
    """
    Consolidated tests for get_current_user dependency.

    Tests token validation and user retrieval.
    """

    def test_get_current_user_success(self, session, sample_user):
        """
        Test successful authentication with valid token.

        Scenarios:
        - Valid token returns correct user
        - User data is fully loaded
        - Token payload user_id matches returned user
        """
        # Create valid token
        token = create_access_token({
            "user_id": sample_user.user_id,
            "email": sample_user.email,
            "user_type": sample_user.user_type
        })

        # Create credentials object
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )

        # Call dependency
        user = get_current_user(credentials=credentials, db=session)

        # Verify user returned
        assert user is not None
        assert user.user_id == sample_user.user_id
        assert user.email == sample_user.email
        assert user.full_name == sample_user.full_name

    def test_get_current_user_invalid_token(self, session):
        """
        Test authentication failures with invalid tokens.

        Scenarios:
        - Completely invalid token raises 401
        - Tampered token raises 401
        - Empty token raises 401
        """
        invalid_tokens = [
            "invalid_token_string",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            ""
        ]

        for invalid_token in invalid_tokens:
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=invalid_token
            )

            with pytest.raises(HTTPException) as exc_info:
                get_current_user(credentials=credentials, db=session)

            assert exc_info.value.status_code == 401
            assert "Invalid or expired token" in exc_info.value.detail

    def test_get_current_user_nonexistent_user(self, session):
        """
        Test authentication with valid token but non-existent user.

        Scenario:
        - Token is valid but user_id doesn't exist in database
        - Should raise 401 (not 404, to prevent user enumeration)
        """
        # Create token with non-existent user_id
        token = create_access_token({
            "user_id": "00000000-0000-0000-0000-000000000000",
            "email": "nonexistent@example.com",
            "user_type": "coach"
        })

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials, db=session)

        assert exc_info.value.status_code == 401
        assert "User not found" in exc_info.value.detail

    def test_get_current_user_missing_user_id_in_payload(self, session):
        """
        Test authentication with token missing user_id.

        Scenario:
        - Token is valid but doesn't contain user_id claim
        - Should raise 401
        """
        # Create token without user_id
        token = create_access_token({
            "email": "test@example.com",
            "user_type": "coach"
            # Missing user_id!
        })

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=credentials, db=session)

        assert exc_info.value.status_code == 401
        assert "Invalid token payload" in exc_info.value.detail


class TestRequireCoach:
    """
    Consolidated tests for require_coach dependency.

    Tests role-based access control for coaches.
    """

    def test_require_coach_success(self, session, sample_user):
        """
        Test coach access granted for coach users.

        Scenario:
        - User with user_type='coach' passes validation
        - Returns the user instance
        """
        # sample_user is a coach
        assert sample_user.user_type == "coach"

        # Call dependency
        user = require_coach(current_user=sample_user)

        # Should return the same user
        assert user.user_id == sample_user.user_id
        assert user.is_coach() is True

    def test_require_coach_forbidden_for_player(self, session, sample_player_user):
        """
        Test coach access denied for player users.

        Scenario:
        - User with user_type='player' raises 403 Forbidden
        - Error message is clear about access restriction
        """
        # sample_player_user is a player
        assert sample_player_user.user_type == "player"

        with pytest.raises(HTTPException) as exc_info:
            require_coach(current_user=sample_player_user)

        assert exc_info.value.status_code == 403
        assert "only accessible to coaches" in exc_info.value.detail


class TestRequirePlayer:
    """
    Consolidated tests for require_player dependency.

    Tests role-based access control for players.
    """

    def test_require_player_success(self, session, sample_player_user):
        """
        Test player access granted for player users.

        Scenario:
        - User with user_type='player' passes validation
        - Returns the user instance
        """
        # sample_player_user is a player
        assert sample_player_user.user_type == "player"

        # Call dependency
        user = require_player(current_user=sample_player_user)

        # Should return the same user
        assert user.user_id == sample_player_user.user_id
        assert user.is_player() is True

    def test_require_player_forbidden_for_coach(self, session, sample_user):
        """
        Test player access denied for coach users.

        Scenario:
        - User with user_type='coach' raises 403 Forbidden
        - Error message is clear about access restriction
        """
        # sample_user is a coach
        assert sample_user.user_type == "coach"

        with pytest.raises(HTTPException) as exc_info:
            require_player(current_user=sample_user)

        assert exc_info.value.status_code == 403
        assert "only accessible to players" in exc_info.value.detail


class TestDependencyIntegration:
    """
    Integration tests for combined dependency usage.

    Tests realistic scenarios of chained dependencies.
    """

    def test_full_authentication_flow_coach(self, session, sample_user, sample_coach):
        """
        Test complete authentication flow for coach.

        Flow:
        1. Create token for coach
        2. Validate token with get_current_user
        3. Verify coach access with require_coach
        4. Access coach-specific data
        """
        # 1. Create token
        token = create_access_token({
            "user_id": sample_user.user_id,
            "email": sample_user.email,
            "user_type": "coach"
        })

        # 2. Validate token
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        authenticated_user = get_current_user(credentials=credentials, db=session)

        # 3. Verify coach access
        coach_user = require_coach(current_user=authenticated_user)

        # 4. Access coach data
        assert coach_user.coach is not None
        assert coach_user.coach.coach_id == sample_coach.coach_id

    def test_full_authentication_flow_player(self, session, sample_player_user, sample_complete_player):
        """
        Test complete authentication flow for player.

        Flow:
        1. Create token for player
        2. Validate token with get_current_user
        3. Verify player access with require_player
        4. Access player-specific data
        """
        # 1. Create token
        token = create_access_token({
            "user_id": sample_player_user.user_id,
            "email": sample_player_user.email,
            "user_type": "player"
        })

        # 2. Validate token
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        authenticated_user = get_current_user(credentials=credentials, db=session)

        # 3. Verify player access
        player_user = require_player(current_user=authenticated_user)

        # 4. Access player data
        assert player_user.player is not None
        assert player_user.player.player_id == sample_complete_player.player_id

    def test_cross_role_access_denied(self, session, sample_user, sample_player_user):
        """
        Test that roles cannot access each other's endpoints.

        Scenarios:
        - Coach cannot access player-only endpoints
        - Player cannot access coach-only endpoints
        """
        # Coach trying to access player endpoint
        with pytest.raises(HTTPException) as exc_info:
            require_player(current_user=sample_user)
        assert exc_info.value.status_code == 403

        # Player trying to access coach endpoint
        with pytest.raises(HTTPException) as exc_info:
            require_coach(current_user=sample_player_user)
        assert exc_info.value.status_code == 403
