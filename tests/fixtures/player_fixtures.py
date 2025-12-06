"""
Fixtures for player endpoint testing.

Provides test data for:
- Player authentication headers
- Player-specific test scenarios

Most fixtures are reused from coach_fixtures.py:
- sample_match, sample_opponent_club
- sample_player_match_statistics
- sample_player_season_statistics
- sample_training_plan
"""

import pytest
from app.core.security import create_access_token


@pytest.fixture
def auth_headers_player(sample_player_user, sample_complete_player):
    """
    Generate auth headers for authenticated player.

    Uses sample_player_user (User with user_type='player')
    and sample_complete_player (linked Player record).

    Args:
        sample_player_user: User fixture from conftest.py
        sample_complete_player: Player fixture from conftest.py

    Returns:
        dict: Authorization header with Bearer token
    """
    token = create_access_token({
        "user_id": str(sample_player_user.user_id),
        "email": sample_player_user.email,
        "user_type": "player"
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_coach_for_player_tests(sample_user):
    """
    Generate auth headers for coach user (for 403 forbidden tests).

    Used to verify player endpoints reject coach tokens.

    Args:
        sample_user: Coach user fixture from conftest.py

    Returns:
        dict: Authorization header with Bearer token
    """
    token = create_access_token({
        "user_id": str(sample_user.user_id),
        "email": sample_user.email,
        "user_type": "coach"
    })
    return {"Authorization": f"Bearer {token}"}
