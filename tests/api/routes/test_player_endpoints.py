"""
Tests for player API endpoints.

Tests all player endpoints with success and error scenarios:
- Dashboard endpoint (My Stats tab)
- Matches endpoints (list and detail)
- Training endpoints (list, detail, toggle)
- Profile endpoint

Each test follows the pattern:
    # Given: Setup test data and auth
    # When: Call endpoint
    # Then: Assert response status and structure

Run with: pytest tests/api/routes/test_player_endpoints.py -v
"""

from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.core.security import create_access_token


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client(engine):
    """
    Create a test client with database dependency overridden.

    This ensures API endpoints use the test database session
    instead of the real database connection.
    """
    from sqlalchemy.orm import sessionmaker
    from app.models.base import Base

    # Ensure tables exist
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


@pytest.fixture
def auth_headers_player_endpoint(sample_player_user, sample_complete_player):
    """Generate auth headers for authenticated player."""
    token = create_access_token({
        "user_id": str(sample_player_user.user_id),
        "email": sample_player_user.email,
        "user_type": "player"
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_coach_for_player_endpoints(sample_user):
    """Generate auth headers for coach user (for 403 tests)."""
    token = create_access_token({
        "user_id": str(sample_user.user_id),
        "email": sample_user.email,
        "user_type": "coach"
    })
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# DASHBOARD ENDPOINT TESTS
# ============================================================================

class TestPlayerDashboardEndpoint:
    """Tests for GET /api/player/dashboard"""

    def test_get_dashboard_success(
        self,
        client,
        sample_complete_player,
        auth_headers_player_endpoint
    ):
        """Test successful dashboard retrieval."""
        # Given: Authenticated player

        # When: Call dashboard endpoint
        response = client.get("/api/player/dashboard", headers=auth_headers_player_endpoint)

        # Then: Returns 200 with correct structure
        assert response.status_code == 200
        data = response.json()

        assert "player" in data
        assert "attributes" in data
        assert "season_statistics" in data

    def test_get_dashboard_with_statistics(
        self,
        client,
        sample_complete_player,
        sample_player_season_statistics,
        auth_headers_player_endpoint
    ):
        """Test dashboard includes statistics."""
        # Given: Player has season statistics

        # When: Call dashboard endpoint
        response = client.get("/api/player/dashboard", headers=auth_headers_player_endpoint)

        # Then: Statistics are populated
        assert response.status_code == 200
        data = response.json()

        assert data["attributes"]["attacking_rating"] is not None
        assert data["season_statistics"]["general"]["matches_played"] > 0

    def test_get_dashboard_no_token_403(self, client):
        """Test dashboard without token returns 403."""
        # Given: No authentication

        # When: Call dashboard endpoint
        response = client.get("/api/player/dashboard")

        # Then: Returns 403
        assert response.status_code == 403

    def test_get_dashboard_coach_forbidden_403(
        self,
        client,
        sample_club,
        auth_headers_coach_for_player_endpoints
    ):
        """Test dashboard with coach token returns 403."""
        # Given: Coach token

        # When: Call dashboard endpoint
        response = client.get(
            "/api/player/dashboard",
            headers=auth_headers_coach_for_player_endpoints
        )

        # Then: Returns 403
        assert response.status_code == 403


# ============================================================================
# MATCHES ENDPOINT TESTS
# ============================================================================

class TestPlayerMatchesListEndpoint:
    """Tests for GET /api/player/matches"""

    def test_get_matches_success(
        self,
        client,
        sample_complete_player,
        sample_match,
        sample_player_match_statistics,
        auth_headers_player_endpoint
    ):
        """Test successful matches list retrieval."""
        # Given: Player has participated in matches

        # When: Call matches endpoint
        response = client.get("/api/player/matches", headers=auth_headers_player_endpoint)

        # Then: Returns 200 with matches
        assert response.status_code == 200
        data = response.json()

        assert "total_count" in data
        assert "matches" in data
        assert data["total_count"] >= 1

    def test_get_matches_pagination(
        self,
        client,
        sample_complete_player,
        sample_match,
        sample_player_match_statistics,
        auth_headers_player_endpoint
    ):
        """Test matches pagination."""
        # Given: Player has matches

        # When: Call matches with pagination
        response = client.get(
            "/api/player/matches?limit=10&offset=0",
            headers=auth_headers_player_endpoint
        )

        # Then: Returns 200
        assert response.status_code == 200

    def test_get_matches_empty(
        self,
        client,
        sample_complete_player,
        auth_headers_player_endpoint
    ):
        """Test matches when player has none."""
        # Given: Player has no match statistics
        # (no sample_player_match_statistics)

        # When: Call matches endpoint
        response = client.get("/api/player/matches", headers=auth_headers_player_endpoint)

        # Then: Returns 200 with empty list
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["matches"] == []

    def test_get_matches_no_token_403(self, client):
        """Test matches without token returns 403."""
        response = client.get("/api/player/matches")
        assert response.status_code == 403


class TestPlayerMatchDetailEndpoint:
    """Tests for GET /api/player/matches/{match_id}"""

    def test_get_match_detail_success(
        self,
        client,
        sample_complete_player,
        sample_match,
        sample_player_match_statistics,
        auth_headers_player_endpoint
    ):
        """Test successful match detail retrieval."""
        # Given: Player participated in match

        # When: Call match detail endpoint
        response = client.get(
            f"/api/player/matches/{sample_match.match_id}",
            headers=auth_headers_player_endpoint
        )

        # Then: Returns 200 with complete structure
        assert response.status_code == 200
        data = response.json()

        assert "match" in data
        assert "teams" in data
        assert "player_summary" in data
        assert "statistics" in data

    def test_get_match_detail_not_participated_404(
        self,
        client,
        sample_complete_player,
        sample_match,
        auth_headers_player_endpoint
    ):
        """Test match detail when player didn't participate."""
        # Given: Match exists but player has no stats
        # (no sample_player_match_statistics)

        # When: Call match detail endpoint
        response = client.get(
            f"/api/player/matches/{sample_match.match_id}",
            headers=auth_headers_player_endpoint
        )

        # Then: Returns 404 (not found/didn't participate)
        assert response.status_code in [403, 404]

    def test_get_match_detail_not_found_404(
        self,
        client,
        sample_complete_player,
        auth_headers_player_endpoint
    ):
        """Test match detail with non-existent match."""
        # Given: Random match ID
        random_match_id = uuid4()

        # When: Call match detail endpoint
        response = client.get(
            f"/api/player/matches/{random_match_id}",
            headers=auth_headers_player_endpoint
        )

        # Then: Returns 404
        assert response.status_code in [403, 404]

    def test_get_match_detail_no_token_403(self, client, sample_match):
        """Test match detail without token returns 403."""
        response = client.get(f"/api/player/matches/{sample_match.match_id}")
        assert response.status_code == 403


# ============================================================================
# TRAINING LIST ENDPOINT TESTS
# ============================================================================

class TestPlayerTrainingListEndpoint:
    """Tests for GET /api/player/training"""

    def test_get_training_plans_success(
        self,
        client,
        sample_complete_player,
        sample_training_plan,
        auth_headers_player_endpoint
    ):
        """Test successful training plans list retrieval."""
        # Given: Player has training plans

        # When: Call training endpoint
        response = client.get("/api/player/training", headers=auth_headers_player_endpoint)

        # Then: Returns 200 with plans
        assert response.status_code == 200
        data = response.json()

        assert "training_plans" in data
        assert len(data["training_plans"]) >= 1

    def test_get_training_plans_empty(
        self,
        client,
        sample_complete_player,
        auth_headers_player_endpoint
    ):
        """Test training plans when player has none."""
        # Given: Player has no training plans
        # (no sample_training_plan)

        # When: Call training endpoint
        response = client.get("/api/player/training", headers=auth_headers_player_endpoint)

        # Then: Returns 200 with empty list
        assert response.status_code == 200
        data = response.json()
        assert data["training_plans"] == []

    def test_get_training_plans_no_token_403(self, client):
        """Test training plans without token returns 403."""
        response = client.get("/api/player/training")
        assert response.status_code == 403


# ============================================================================
# TRAINING DETAIL ENDPOINT TESTS
# ============================================================================

class TestPlayerTrainingDetailEndpoint:
    """Tests for GET /api/player/training/{plan_id}"""

    def test_get_training_plan_success(
        self,
        client,
        sample_complete_player,
        sample_training_plan,
        auth_headers_player_endpoint
    ):
        """Test successful training plan detail retrieval."""
        # Given: Training plan exists
        plan = sample_training_plan["plan"]

        # When: Call training plan detail endpoint
        response = client.get(
            f"/api/player/training/{plan.plan_id}",
            headers=auth_headers_player_endpoint
        )

        # Then: Returns 200 with complete structure
        assert response.status_code == 200
        data = response.json()

        assert "plan" in data
        assert "progress" in data
        assert "exercises" in data
        assert "coach_notes" in data

    def test_get_training_plan_includes_exercises(
        self,
        client,
        sample_complete_player,
        sample_training_plan,
        auth_headers_player_endpoint
    ):
        """Test training plan includes exercises."""
        # Given: Plan has exercises
        plan = sample_training_plan["plan"]
        exercises = sample_training_plan["exercises"]

        # When: Call training plan detail endpoint
        response = client.get(
            f"/api/player/training/{plan.plan_id}",
            headers=auth_headers_player_endpoint
        )

        # Then: Exercises are included
        assert response.status_code == 200
        data = response.json()
        assert len(data["exercises"]) == len(exercises)

    def test_get_training_plan_not_found_404(
        self,
        client,
        sample_complete_player,
        auth_headers_player_endpoint
    ):
        """Test training plan with non-existent plan."""
        # Given: Random plan ID
        random_plan_id = uuid4()

        # When: Call training plan detail endpoint
        response = client.get(
            f"/api/player/training/{random_plan_id}",
            headers=auth_headers_player_endpoint
        )

        # Then: Returns 404
        assert response.status_code == 404

    def test_get_training_plan_no_token_403(self, client, sample_training_plan):
        """Test training plan without token returns 403."""
        plan = sample_training_plan["plan"]
        response = client.get(f"/api/player/training/{plan.plan_id}")
        assert response.status_code == 403


# ============================================================================
# TOGGLE EXERCISE ENDPOINT TESTS
# ============================================================================

class TestToggleExerciseEndpoint:
    """Tests for PUT /api/player/training/exercises/{exercise_id}/toggle"""

    def test_toggle_exercise_success(
        self,
        client,
        sample_complete_player,
        sample_training_plan,
        auth_headers_player_endpoint
    ):
        """Test successful exercise toggle."""
        # Given: Exercise exists
        exercise = sample_training_plan["exercises"][0]

        # When: Toggle exercise
        response = client.put(
            f"/api/player/training/exercises/{exercise.exercise_id}/toggle",
            json={"completed": not exercise.completed},
            headers=auth_headers_player_endpoint
        )

        # Then: Returns 200 with updated status
        assert response.status_code == 200
        data = response.json()

        assert "exercise_id" in data
        assert "completed" in data
        assert "plan_progress" in data

    def test_toggle_exercise_returns_progress(
        self,
        client,
        sample_complete_player,
        sample_training_plan,
        auth_headers_player_endpoint
    ):
        """Test toggle returns updated progress."""
        # Given: Exercise exists
        exercise = sample_training_plan["exercises"][0]

        # When: Toggle exercise
        response = client.put(
            f"/api/player/training/exercises/{exercise.exercise_id}/toggle",
            json={"completed": True},
            headers=auth_headers_player_endpoint
        )

        # Then: Returns plan progress
        assert response.status_code == 200
        data = response.json()

        assert "plan_progress" in data
        assert "plan_id" in data["plan_progress"]
        assert "total_exercises" in data["plan_progress"]
        assert "completed_exercises" in data["plan_progress"]
        assert "progress_percentage" in data["plan_progress"]
        assert "plan_status" in data["plan_progress"]

    def test_toggle_exercise_not_found_404(
        self,
        client,
        sample_complete_player,
        auth_headers_player_endpoint
    ):
        """Test toggle with non-existent exercise."""
        # Given: Random exercise ID
        random_exercise_id = uuid4()

        # When: Toggle exercise
        response = client.put(
            f"/api/player/training/exercises/{random_exercise_id}/toggle",
            json={"completed": True},
            headers=auth_headers_player_endpoint
        )

        # Then: Returns 404
        assert response.status_code == 404

    def test_toggle_exercise_no_token_403(self, client, sample_training_plan):
        """Test toggle without token returns 403."""
        exercise = sample_training_plan["exercises"][0]
        response = client.put(
            f"/api/player/training/exercises/{exercise.exercise_id}/toggle",
            json={"completed": True}
        )
        assert response.status_code == 403


# ============================================================================
# PROFILE ENDPOINT TESTS
# ============================================================================

class TestPlayerProfileEndpoint:
    """Tests for GET /api/player/profile"""

    def test_get_profile_success(
        self,
        client,
        sample_complete_player,
        auth_headers_player_endpoint
    ):
        """Test successful profile retrieval."""
        # Given: Authenticated player

        # When: Call profile endpoint
        response = client.get("/api/player/profile", headers=auth_headers_player_endpoint)

        # Then: Returns 200 with correct structure
        assert response.status_code == 200
        data = response.json()

        assert "player" in data
        assert "club" in data
        assert "season_summary" in data

    def test_get_profile_includes_email(
        self,
        client,
        sample_complete_player,
        sample_player_user,
        auth_headers_player_endpoint
    ):
        """Test profile includes email."""
        # Given: Linked player

        # When: Call profile endpoint
        response = client.get("/api/player/profile", headers=auth_headers_player_endpoint)

        # Then: Email is included
        assert response.status_code == 200
        data = response.json()
        assert data["player"]["email"] == sample_player_user.email

    def test_get_profile_with_statistics(
        self,
        client,
        sample_complete_player,
        sample_player_season_statistics,
        auth_headers_player_endpoint
    ):
        """Test profile includes season summary."""
        # Given: Player has season statistics

        # When: Call profile endpoint
        response = client.get("/api/player/profile", headers=auth_headers_player_endpoint)

        # Then: Season summary is populated
        assert response.status_code == 200
        data = response.json()
        assert data["season_summary"]["matches_played"] > 0

    def test_get_profile_no_token_403(self, client):
        """Test profile without token returns 403."""
        response = client.get("/api/player/profile")
        assert response.status_code == 403

    def test_get_profile_coach_forbidden_403(
        self,
        client,
        sample_club,
        auth_headers_coach_for_player_endpoints
    ):
        """Test profile with coach token returns 403."""
        response = client.get(
            "/api/player/profile",
            headers=auth_headers_coach_for_player_endpoints
        )
        assert response.status_code == 403
