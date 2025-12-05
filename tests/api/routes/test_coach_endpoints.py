"""
Tests for coach API endpoints.

Tests all coach endpoints with success and error scenarios:
- Profile and Dashboard endpoints
- Match endpoints
- Player endpoints
- Training plan endpoints

Each test follows the pattern:
    # Given: Setup test data and auth
    # When: Call endpoint
    # Then: Assert response status and structure

Run with: pytest tests/api/routes/test_coach_endpoints.py -v
"""

from datetime import date
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
def auth_headers_coach(sample_user):
    """Generate auth headers for coach user."""
    token = create_access_token({
        "user_id": str(sample_user.user_id),
        "email": sample_user.email,
        "user_type": "coach"
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_player(sample_player_user):
    """Generate auth headers for player user (for 403 tests)."""
    token = create_access_token({
        "user_id": str(sample_player_user.user_id),
        "email": sample_player_user.email,
        "user_type": "player"
    })
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# PROFILE & DASHBOARD ENDPOINT TESTS
# ============================================================================

class TestCoachProfileEndpoint:
    """Tests for GET /api/coach/profile"""

    def test_get_profile_success(self, client, sample_club, auth_headers_coach):
        """Test successful profile retrieval."""
        # Given: Authenticated coach with club
        # (provided by fixtures)

        # When: Call profile endpoint
        response = client.get("/api/coach/profile", headers=auth_headers_coach)

        # Then: Returns 200 with correct structure
        assert response.status_code == 200
        data = response.json()

        assert "coach" in data
        assert "club" in data
        assert "club_stats" in data

        assert "full_name" in data["coach"]
        assert "email" in data["coach"]
        assert "club_name" in data["club"]

    def test_get_profile_with_statistics(
        self,
        client,
        sample_club,
        sample_club_season_statistics,
        auth_headers_coach
    ):
        """Test profile includes club statistics."""
        # Given: Club has statistics
        # (provided by fixtures)

        # When: Call profile endpoint
        response = client.get("/api/coach/profile", headers=auth_headers_coach)

        # Then: Statistics are included
        assert response.status_code == 200
        data = response.json()

        assert data["club_stats"]["total_matches"] > 0

    def test_get_profile_no_token_403(self, client):
        """Test profile endpoint without token."""
        # Given: No authentication token

        # When: Call profile endpoint
        response = client.get("/api/coach/profile")

        # Then: Returns 403
        assert response.status_code == 403

    def test_get_profile_player_forbidden_403(self, client, auth_headers_player):
        """Test profile endpoint with player token."""
        # Given: Player authentication token

        # When: Call profile endpoint
        response = client.get("/api/coach/profile", headers=auth_headers_player)

        # Then: Returns 403
        assert response.status_code == 403


class TestCoachDashboardEndpoint:
    """Tests for GET /api/coach/dashboard"""

    def test_get_dashboard_success(self, client, sample_club, auth_headers_coach):
        """Test successful dashboard retrieval."""
        # Given: Authenticated coach with club
        # (provided by fixtures)

        # When: Call dashboard endpoint
        response = client.get("/api/coach/dashboard", headers=auth_headers_coach)

        # Then: Returns 200 with correct structure
        assert response.status_code == 200
        data = response.json()

        assert "coach" in data
        assert "club" in data
        assert "season_record" in data
        assert "team_form" in data
        assert "matches" in data
        assert "statistics" in data

    def test_get_dashboard_with_statistics(
        self,
        client,
        sample_club,
        sample_club_season_statistics,
        auth_headers_coach
    ):
        """Test dashboard includes statistics."""
        # Given: Club has statistics
        # (provided by fixtures)

        # When: Call dashboard endpoint
        response = client.get("/api/coach/dashboard", headers=auth_headers_coach)

        # Then: Statistics are populated
        assert response.status_code == 200
        data = response.json()

        assert data["season_record"]["wins"] > 0
        assert "attacking" in data["statistics"]
        assert "defending" in data["statistics"]

    def test_get_dashboard_with_matches(
        self,
        client,
        sample_club,
        sample_match,
        sample_club_season_statistics,
        auth_headers_coach
    ):
        """Test dashboard includes matches."""
        # Given: Club has matches
        # (provided by fixtures)

        # When: Call dashboard endpoint
        response = client.get("/api/coach/dashboard", headers=auth_headers_coach)

        # Then: Matches are included
        assert response.status_code == 200
        data = response.json()

        assert data["matches"]["total_count"] >= 1
        assert len(data["matches"]["matches"]) >= 1

    def test_get_dashboard_pagination(
        self,
        client,
        sample_club,
        sample_club_season_statistics,
        auth_headers_coach
    ):
        """Test dashboard pagination works."""
        # Given: Authenticated coach

        # When: Call dashboard with pagination params
        response = client.get(
            "/api/coach/dashboard?matches_limit=5&matches_offset=0",
            headers=auth_headers_coach
        )

        # Then: Returns 200
        assert response.status_code == 200
        data = response.json()
        assert "matches" in data

    def test_get_dashboard_no_token_403(self, client):
        """Test dashboard endpoint without token."""
        # Given: No authentication token

        # When: Call dashboard endpoint
        response = client.get("/api/coach/dashboard")

        # Then: Returns 403
        assert response.status_code == 403

    def test_get_dashboard_player_forbidden_403(self, client, auth_headers_player):
        """Test dashboard endpoint with player token."""
        # Given: Player authentication token

        # When: Call dashboard endpoint
        response = client.get("/api/coach/dashboard", headers=auth_headers_player)

        # Then: Returns 403
        assert response.status_code == 403


# ============================================================================
# MATCH ENDPOINT TESTS
# ============================================================================

class TestMatchDetailEndpoint:
    """Tests for GET /api/coach/matches/{match_id}"""

    def test_get_match_detail_success(
        self,
        client,
        sample_match,
        auth_headers_coach
    ):
        """Test successful match detail retrieval."""
        # Given: Match exists
        # (provided by fixtures)

        # When: Call match detail endpoint
        response = client.get(
            f"/api/coach/matches/{sample_match.match_id}",
            headers=auth_headers_coach
        )

        # Then: Returns 200 with correct structure
        assert response.status_code == 200
        data = response.json()

        assert "match" in data
        assert "teams" in data
        assert "summary" in data
        assert "statistics" in data
        assert "lineup" in data

    def test_get_match_detail_with_goals(
        self,
        client,
        sample_match,
        sample_goals,
        auth_headers_coach
    ):
        """Test match detail includes goals."""
        # Given: Match has goals
        # (provided by fixtures)

        # When: Call match detail endpoint
        response = client.get(
            f"/api/coach/matches/{sample_match.match_id}",
            headers=auth_headers_coach
        )

        # Then: Goals are included
        assert response.status_code == 200
        data = response.json()

        assert len(data["summary"]["goal_scorers"]) > 0

    def test_get_match_detail_with_statistics(
        self,
        client,
        sample_match,
        sample_match_statistics,
        auth_headers_coach
    ):
        """Test match detail includes statistics."""
        # Given: Match has statistics
        # (provided by fixtures)

        # When: Call match detail endpoint
        response = client.get(
            f"/api/coach/matches/{sample_match.match_id}",
            headers=auth_headers_coach
        )

        # Then: Statistics are populated
        assert response.status_code == 200
        data = response.json()

        assert data["statistics"]["match_overview"]["ball_possession"]["our_team"] > 0

    def test_get_match_detail_not_found_404(self, client, auth_headers_coach):
        """Test match detail with non-existent match."""
        # Given: Random match ID
        random_match_id = uuid4()

        # When: Call match detail endpoint
        response = client.get(
            f"/api/coach/matches/{random_match_id}",
            headers=auth_headers_coach
        )

        # Then: Returns 404
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_match_detail_no_token_403(self, client, sample_match):
        """Test match detail without token."""
        # Given: No authentication token

        # When: Call match detail endpoint
        response = client.get(f"/api/coach/matches/{sample_match.match_id}")

        # Then: Returns 403
        assert response.status_code == 403

    def test_get_match_detail_player_forbidden_403(
        self,
        client,
        sample_match,
        auth_headers_player
    ):
        """Test match detail with player token."""
        # Given: Player authentication token

        # When: Call match detail endpoint
        response = client.get(
            f"/api/coach/matches/{sample_match.match_id}",
            headers=auth_headers_player
        )

        # Then: Returns 403
        assert response.status_code == 403


# ============================================================================
# PLAYER ENDPOINT TESTS
# ============================================================================

class TestPlayersListEndpoint:
    """Tests for GET /api/coach/players"""

    def test_get_players_list_success(
        self,
        client,
        sample_complete_player,
        auth_headers_coach
    ):
        """Test successful players list retrieval."""
        # Given: Club has players
        # (provided by fixtures)

        # When: Call players list endpoint
        response = client.get("/api/coach/players", headers=auth_headers_coach)

        # Then: Returns 200 with correct structure
        assert response.status_code == 200
        data = response.json()

        assert "summary" in data
        assert "players" in data

        assert "total_players" in data["summary"]
        assert "joined" in data["summary"]
        assert "pending" in data["summary"]

    def test_get_players_list_includes_players(
        self,
        client,
        sample_complete_player,
        auth_headers_coach
    ):
        """Test players list includes player data."""
        # Given: Club has players
        # (provided by fixtures)

        # When: Call players list endpoint
        response = client.get("/api/coach/players", headers=auth_headers_coach)

        # Then: Players are included
        assert response.status_code == 200
        data = response.json()

        assert len(data["players"]) >= 1
        player = data["players"][0]
        assert "player_id" in player
        assert "player_name" in player
        assert "jersey_number" in player

    def test_get_players_list_no_token_403(self, client):
        """Test players list without token."""
        # Given: No authentication token

        # When: Call players list endpoint
        response = client.get("/api/coach/players")

        # Then: Returns 403
        assert response.status_code == 403

    def test_get_players_list_player_forbidden_403(self, client, auth_headers_player):
        """Test players list with player token."""
        # Given: Player authentication token

        # When: Call players list endpoint
        response = client.get("/api/coach/players", headers=auth_headers_player)

        # Then: Returns 403
        assert response.status_code == 403


class TestPlayerDetailEndpoint:
    """Tests for GET /api/coach/players/{player_id}"""

    def test_get_player_detail_success(
        self,
        client,
        sample_complete_player,
        auth_headers_coach
    ):
        """Test successful player detail retrieval."""
        # Given: Player exists
        # (provided by fixtures)

        # When: Call player detail endpoint
        response = client.get(
            f"/api/coach/players/{sample_complete_player.player_id}",
            headers=auth_headers_coach
        )

        # Then: Returns 200 with correct structure
        assert response.status_code == 200
        data = response.json()

        assert "player" in data
        assert "attributes" in data
        assert "season_statistics" in data
        assert "matches" in data
        assert "training_plans" in data

    def test_get_player_detail_with_statistics(
        self,
        client,
        sample_complete_player,
        sample_player_season_statistics,
        auth_headers_coach
    ):
        """Test player detail includes statistics."""
        # Given: Player has statistics
        # (provided by fixtures)

        # When: Call player detail endpoint
        response = client.get(
            f"/api/coach/players/{sample_complete_player.player_id}",
            headers=auth_headers_coach
        )

        # Then: Statistics are populated
        assert response.status_code == 200
        data = response.json()

        assert data["attributes"]["attacking_rating"] is not None
        assert data["season_statistics"]["general"]["matches_played"] > 0

    def test_get_player_detail_invite_code_unlinked(
        self,
        client,
        sample_incomplete_player,
        auth_headers_coach
    ):
        """Test player detail includes invite_code for unlinked players."""
        # Given: Unlinked player
        # (provided by fixtures)

        # When: Call player detail endpoint
        response = client.get(
            f"/api/coach/players/{sample_incomplete_player.player_id}",
            headers=auth_headers_coach
        )

        # Then: Invite code is included
        assert response.status_code == 200
        data = response.json()

        assert data["invite_code"] is not None

    def test_get_player_detail_no_invite_code_linked(
        self,
        client,
        sample_complete_player,
        auth_headers_coach
    ):
        """Test player detail excludes invite_code for linked players."""
        # Given: Linked player
        # (provided by fixtures)

        # When: Call player detail endpoint
        response = client.get(
            f"/api/coach/players/{sample_complete_player.player_id}",
            headers=auth_headers_coach
        )

        # Then: Invite code is None
        assert response.status_code == 200
        data = response.json()

        assert data["invite_code"] is None

    def test_get_player_detail_not_found_404(self, client, auth_headers_coach):
        """Test player detail with non-existent player."""
        # Given: Random player ID
        random_player_id = uuid4()

        # When: Call player detail endpoint
        response = client.get(
            f"/api/coach/players/{random_player_id}",
            headers=auth_headers_coach
        )

        # Then: Returns 404
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_player_detail_no_token_403(self, client, sample_complete_player):
        """Test player detail without token."""
        # Given: No authentication token

        # When: Call player detail endpoint
        response = client.get(f"/api/coach/players/{sample_complete_player.player_id}")

        # Then: Returns 403
        assert response.status_code == 403

    def test_get_player_detail_player_forbidden_403(
        self,
        client,
        sample_complete_player,
        auth_headers_player
    ):
        """Test player detail with player token."""
        # Given: Player authentication token

        # When: Call player detail endpoint
        response = client.get(
            f"/api/coach/players/{sample_complete_player.player_id}",
            headers=auth_headers_player
        )

        # Then: Returns 403
        assert response.status_code == 403


class TestPlayerMatchPerformanceEndpoint:
    """Tests for GET /api/coach/players/{player_id}/matches/{match_id}"""

    def test_get_player_match_performance_success(
        self,
        client,
        sample_complete_player,
        sample_match,
        sample_player_match_statistics,
        auth_headers_coach
    ):
        """Test successful player match performance retrieval."""
        # Given: Player has match statistics
        # (provided by fixtures)

        # When: Call player match performance endpoint
        response = client.get(
            f"/api/coach/players/{sample_complete_player.player_id}/matches/{sample_match.match_id}",
            headers=auth_headers_coach
        )

        # Then: Returns 200 with correct structure
        assert response.status_code == 200
        data = response.json()

        assert "match" in data
        assert "teams" in data
        assert "player_summary" in data
        assert "statistics" in data

    def test_get_player_match_performance_includes_all_stats(
        self,
        client,
        sample_complete_player,
        sample_match,
        sample_player_match_statistics,
        auth_headers_coach
    ):
        """Test player match performance includes all statistics."""
        # Given: Player has match statistics
        # (provided by fixtures)

        # When: Call player match performance endpoint
        response = client.get(
            f"/api/coach/players/{sample_complete_player.player_id}/matches/{sample_match.match_id}",
            headers=auth_headers_coach
        )

        # Then: All statistics are present
        assert response.status_code == 200
        data = response.json()

        assert "attacking" in data["statistics"]
        assert "passing" in data["statistics"]
        assert "defending" in data["statistics"]

    def test_get_player_match_performance_player_not_found_404(
        self,
        client,
        sample_match,
        auth_headers_coach
    ):
        """Test player match performance with non-existent player."""
        # Given: Random player ID
        random_player_id = uuid4()

        # When: Call player match performance endpoint
        response = client.get(
            f"/api/coach/players/{random_player_id}/matches/{sample_match.match_id}",
            headers=auth_headers_coach
        )

        # Then: Returns 404
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_player_match_performance_match_not_found_404(
        self,
        client,
        sample_complete_player,
        auth_headers_coach
    ):
        """Test player match performance with non-existent match."""
        # Given: Random match ID
        random_match_id = uuid4()

        # When: Call player match performance endpoint
        response = client.get(
            f"/api/coach/players/{sample_complete_player.player_id}/matches/{random_match_id}",
            headers=auth_headers_coach
        )

        # Then: Returns 404
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_player_match_performance_no_token_403(
        self,
        client,
        sample_complete_player,
        sample_match
    ):
        """Test player match performance without token."""
        # Given: No authentication token

        # When: Call player match performance endpoint
        response = client.get(
            f"/api/coach/players/{sample_complete_player.player_id}/matches/{sample_match.match_id}"
        )

        # Then: Returns 403
        assert response.status_code == 403


# ============================================================================
# TRAINING PLAN ENDPOINT TESTS
# ============================================================================

class TestGenerateAITrainingPlanEndpoint:
    """Tests for POST /api/coach/training-plans/generate-ai"""

    def test_generate_ai_plan_success(
        self,
        client,
        sample_complete_player,
        auth_headers_coach
    ):
        """Test successful AI plan generation."""
        # Given: Player exists
        # (provided by fixtures)

        # When: Call generate AI plan endpoint
        response = client.post(
            "/api/coach/training-plans/generate-ai",
            json={"player_id": str(sample_complete_player.player_id)},
            headers=auth_headers_coach
        )

        # Then: Returns 200 with plan data
        assert response.status_code == 200
        data = response.json()

        assert "player_name" in data
        assert "plan_name" in data
        assert "exercises" in data

    def test_generate_ai_plan_includes_exercises(
        self,
        client,
        sample_complete_player,
        auth_headers_coach
    ):
        """Test AI plan includes exercises."""
        # Given: Player exists
        # (provided by fixtures)

        # When: Call generate AI plan endpoint
        response = client.post(
            "/api/coach/training-plans/generate-ai",
            json={"player_id": str(sample_complete_player.player_id)},
            headers=auth_headers_coach
        )

        # Then: Exercises are included
        assert response.status_code == 200
        data = response.json()

        assert len(data["exercises"]) > 0

    def test_generate_ai_plan_player_not_found_404(self, client, auth_headers_coach):
        """Test generate AI plan with non-existent player."""
        # Given: Random player ID
        random_player_id = uuid4()

        # When: Call generate AI plan endpoint
        response = client.post(
            "/api/coach/training-plans/generate-ai",
            json={"player_id": str(random_player_id)},
            headers=auth_headers_coach
        )

        # Then: Returns 404
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_generate_ai_plan_no_token_403(self, client, sample_complete_player):
        """Test generate AI plan without token."""
        # Given: No authentication token

        # When: Call generate AI plan endpoint
        response = client.post(
            "/api/coach/training-plans/generate-ai",
            json={"player_id": str(sample_complete_player.player_id)}
        )

        # Then: Returns 403
        assert response.status_code == 403


class TestCreateTrainingPlanEndpoint:
    """Tests for POST /api/coach/training-plans"""

    def test_create_training_plan_success(
        self,
        client,
        sample_complete_player,
        auth_headers_coach
    ):
        """Test successful training plan creation."""
        # Given: Valid plan data
        plan_data = {
            "player_id": str(sample_complete_player.player_id),
            "plan_name": "Test Training Plan",
            "duration": "2 weeks",
            "coach_notes": "Focus on speed",
            "exercises": [
                {
                    "exercise_name": "Sprint Drills",
                    "description": "100m sprints",
                    "sets": "3",
                    "reps": "5",
                    "duration_minutes": "15",
                    "exercise_order": 1
                }
            ]
        }

        # When: Call create training plan endpoint
        response = client.post(
            "/api/coach/training-plans",
            json=plan_data,
            headers=auth_headers_coach
        )

        # Then: Returns 201 with plan data
        assert response.status_code == 201
        data = response.json()

        assert "plan_id" in data
        assert data["plan_name"] == "Test Training Plan"
        assert data["status"] == "pending"

    def test_create_training_plan_with_exercises(
        self,
        client,
        sample_complete_player,
        auth_headers_coach
    ):
        """Test creating plan with multiple exercises."""
        # Given: Plan data with multiple exercises
        plan_data = {
            "player_id": str(sample_complete_player.player_id),
            "plan_name": "Complex Plan",
            "exercises": [
                {
                    "exercise_name": "Exercise 1",
                    "exercise_order": 1
                },
                {
                    "exercise_name": "Exercise 2",
                    "exercise_order": 2
                }
            ]
        }

        # When: Call create training plan endpoint
        response = client.post(
            "/api/coach/training-plans",
            json=plan_data,
            headers=auth_headers_coach
        )

        # Then: Returns 201 with exercise count
        assert response.status_code == 201
        data = response.json()

        assert data["exercise_count"] == 2

    def test_create_training_plan_player_not_found_error(self, client, auth_headers_coach):
        """Test create training plan with non-existent player."""
        # Given: Random player ID
        plan_data = {
            "player_id": str(uuid4()),
            "plan_name": "Test Plan",
            "exercises": []
        }

        # When: Call create training plan endpoint
        response = client.post(
            "/api/coach/training-plans",
            json=plan_data,
            headers=auth_headers_coach
        )

        # Then: Returns 404 or 422 (validation error)
        assert response.status_code in [404, 422]
        if response.status_code == 404:
            assert "not found" in response.json()["detail"].lower()

    def test_create_training_plan_no_token_403(self, client, sample_complete_player):
        """Test create training plan without token."""
        # Given: No authentication token
        plan_data = {
            "player_id": str(sample_complete_player.player_id),
            "plan_name": "Test Plan",
            "exercises": []
        }

        # When: Call create training plan endpoint
        response = client.post(
            "/api/coach/training-plans",
            json=plan_data
        )

        # Then: Returns 403
        assert response.status_code == 403


class TestGetTrainingPlanEndpoint:
    """Tests for GET /api/coach/training-plans/{plan_id}"""

    def test_get_training_plan_success(
        self,
        client,
        sample_training_plan,
        auth_headers_coach
    ):
        """Test successful training plan retrieval."""
        # Given: Training plan exists
        plan = sample_training_plan["plan"]

        # When: Call get training plan endpoint
        response = client.get(
            f"/api/coach/training-plans/{plan.plan_id}",
            headers=auth_headers_coach
        )

        # Then: Returns 200 with plan data
        assert response.status_code == 200
        data = response.json()

        assert "plan" in data
        assert "progress" in data
        assert "exercises" in data

    def test_get_training_plan_includes_progress(
        self,
        client,
        sample_training_plan,
        auth_headers_coach
    ):
        """Test training plan includes progress."""
        # Given: Training plan with exercises
        plan = sample_training_plan["plan"]

        # When: Call get training plan endpoint
        response = client.get(
            f"/api/coach/training-plans/{plan.plan_id}",
            headers=auth_headers_coach
        )

        # Then: Progress is included
        assert response.status_code == 200
        data = response.json()

        assert "percentage" in data["progress"]
        assert "completed_exercises" in data["progress"]
        assert "total_exercises" in data["progress"]

    def test_get_training_plan_includes_exercises(
        self,
        client,
        sample_training_plan,
        auth_headers_coach
    ):
        """Test training plan includes exercises."""
        # Given: Training plan with exercises
        plan = sample_training_plan["plan"]

        # When: Call get training plan endpoint
        response = client.get(
            f"/api/coach/training-plans/{plan.plan_id}",
            headers=auth_headers_coach
        )

        # Then: Exercises are included
        assert response.status_code == 200
        data = response.json()

        assert len(data["exercises"]) > 0

    def test_get_training_plan_not_found_404(self, client, auth_headers_coach):
        """Test get training plan with non-existent plan."""
        # Given: Random plan ID
        random_plan_id = uuid4()

        # When: Call get training plan endpoint
        response = client.get(
            f"/api/coach/training-plans/{random_plan_id}",
            headers=auth_headers_coach
        )

        # Then: Returns 404
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_training_plan_no_token_403(self, client, sample_training_plan):
        """Test get training plan without token."""
        # Given: No authentication token
        plan = sample_training_plan["plan"]

        # When: Call get training plan endpoint
        response = client.get(f"/api/coach/training-plans/{plan.plan_id}")

        # Then: Returns 403
        assert response.status_code == 403


class TestUpdateTrainingPlanEndpoint:
    """Tests for PUT /api/coach/training-plans/{plan_id}"""

    def test_update_training_plan_success(
        self,
        client,
        sample_training_plan,
        auth_headers_coach
    ):
        """Test successful training plan update."""
        # Given: Training plan exists
        plan = sample_training_plan["plan"]
        update_data = {
            "plan_name": "Updated Plan Name",
            "duration": "3 weeks"
        }

        # When: Call update training plan endpoint
        response = client.put(
            f"/api/coach/training-plans/{plan.plan_id}",
            json=update_data,
            headers=auth_headers_coach
        )

        # Then: Returns 200
        assert response.status_code == 200
        data = response.json()

        assert data["plan_name"] == "Updated Plan Name"
        assert data["updated"] is True

    def test_update_training_plan_exercises(
        self,
        client,
        sample_training_plan,
        auth_headers_coach
    ):
        """Test updating plan exercises."""
        # Given: Training plan with exercises
        plan = sample_training_plan["plan"]
        exercises = sample_training_plan["exercises"]

        update_data = {
            "exercises": [
                {
                    "exercise_id": str(exercises[0].exercise_id),
                    "exercise_name": "Updated Exercise",
                    "exercise_order": 1
                }
            ]
        }

        # When: Call update training plan endpoint
        response = client.put(
            f"/api/coach/training-plans/{plan.plan_id}",
            json=update_data,
            headers=auth_headers_coach
        )

        # Then: Returns 200
        assert response.status_code == 200
        data = response.json()

        assert data["updated"] is True

    def test_update_training_plan_not_found_404(self, client, auth_headers_coach):
        """Test update training plan with non-existent plan."""
        # Given: Random plan ID
        random_plan_id = uuid4()
        update_data = {"plan_name": "Test"}

        # When: Call update training plan endpoint
        response = client.put(
            f"/api/coach/training-plans/{random_plan_id}",
            json=update_data,
            headers=auth_headers_coach
        )

        # Then: Returns 404
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_training_plan_no_token_403(self, client, sample_training_plan):
        """Test update training plan without token."""
        # Given: No authentication token
        plan = sample_training_plan["plan"]
        update_data = {"plan_name": "Test"}

        # When: Call update training plan endpoint
        response = client.put(
            f"/api/coach/training-plans/{plan.plan_id}",
            json=update_data
        )

        # Then: Returns 403
        assert response.status_code == 403


class TestDeleteTrainingPlanEndpoint:
    """Tests for DELETE /api/coach/training-plans/{plan_id}"""

    def test_delete_training_plan_success(
        self,
        client,
        sample_training_plan_empty,
        auth_headers_coach
    ):
        """Test successful training plan deletion."""
        # Given: Training plan exists (use empty plan to avoid cascade complications)
        plan = sample_training_plan_empty

        # When: Call delete training plan endpoint
        response = client.delete(
            f"/api/coach/training-plans/{plan.plan_id}",
            headers=auth_headers_coach
        )

        # Then: Returns 200
        assert response.status_code == 200
        data = response.json()

        assert data["deleted"] is True
        assert data["plan_id"] == str(plan.plan_id)

    def test_delete_training_plan_not_found_404(self, client, auth_headers_coach):
        """Test delete training plan with non-existent plan."""
        # Given: Random plan ID
        random_plan_id = uuid4()

        # When: Call delete training plan endpoint
        response = client.delete(
            f"/api/coach/training-plans/{random_plan_id}",
            headers=auth_headers_coach
        )

        # Then: Returns 404
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_training_plan_no_token_403(self, client, sample_training_plan):
        """Test delete training plan without token."""
        # Given: No authentication token
        plan = sample_training_plan["plan"]

        # When: Call delete training plan endpoint
        response = client.delete(f"/api/coach/training-plans/{plan.plan_id}")

        # Then: Returns 403
        assert response.status_code == 403
