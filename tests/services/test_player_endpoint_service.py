"""
Tests for player endpoint service module.

Tests all player service functions following Given-When-Then pattern:
- Ownership verification functions
- Dashboard service
- Matches services
- Training services
- Profile service
"""

import pytest
from datetime import date, datetime, timezone
from uuid import uuid4
from decimal import Decimal

from app.services import player_endpoint_service
from app.models.player import Player
from app.models.player_season_statistics import PlayerSeasonStatistics
from app.models.player_match_statistics import PlayerMatchStatistics
from app.models.training_plan import TrainingPlan
from app.models.training_exercise import TrainingExercise


class TestVerifyPlayerMatchParticipation:
    """Test verify_player_match_participation() function."""

    def test_verify_participation_success(
        self,
        session,
        sample_complete_player,
        sample_match,
        sample_player_match_statistics
    ):
        """Test successful participation verification."""
        # Given: Player has match statistics

        # When: Verify participation
        result = player_endpoint_service.verify_player_match_participation(
            session,
            sample_complete_player.player_id,
            sample_match.match_id
        )

        # Then: Returns player match statistics
        assert result.player_id == sample_complete_player.player_id
        assert result.match_id == sample_match.match_id

    def test_verify_participation_match_not_found(
        self,
        session,
        sample_complete_player
    ):
        """Test participation verification when match doesn't exist."""
        # Given: Random match ID (doesn't exist)
        random_match_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            player_endpoint_service.verify_player_match_participation(
                session,
                sample_complete_player.player_id,
                random_match_id
            )

        assert "not found" in str(exc_info.value).lower()

    def test_verify_participation_player_not_in_match(
        self,
        session,
        sample_complete_player,
        sample_match
    ):
        """Test participation verification when player didn't play in match."""
        # Given: Match exists but player has no statistics for it
        # (sample_player_match_statistics fixture NOT included)

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            player_endpoint_service.verify_player_match_participation(
                session,
                sample_complete_player.player_id,
                sample_match.match_id
            )

        error_msg = str(exc_info.value).lower()
        assert "not found" in error_msg or "did not play" in error_msg


class TestVerifyPlayerTrainingPlan:
    """Test verify_player_training_plan() function."""

    def test_verify_plan_ownership_success(
        self,
        session,
        sample_complete_player,
        sample_training_plan
    ):
        """Test successful plan ownership verification."""
        # Given: Training plan belongs to player
        plan = sample_training_plan["plan"]

        # When: Verify ownership
        result = player_endpoint_service.verify_player_training_plan(
            session,
            plan.plan_id,
            sample_complete_player.player_id
        )

        # Then: Returns the plan
        assert result.plan_id == plan.plan_id

    def test_verify_plan_not_found(self, session, sample_complete_player):
        """Test plan verification when plan doesn't exist."""
        # Given: Random plan ID
        random_plan_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            player_endpoint_service.verify_player_training_plan(
                session,
                random_plan_id,
                sample_complete_player.player_id
            )

        assert "not found" in str(exc_info.value).lower()

    def test_verify_plan_wrong_player(
        self,
        session,
        sample_training_plan
    ):
        """Test plan verification with wrong player."""
        # Given: Plan exists but belongs to different player
        plan = sample_training_plan["plan"]
        different_player_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            player_endpoint_service.verify_player_training_plan(
                session,
                plan.plan_id,
                different_player_id
            )

        assert "not assigned" in str(exc_info.value).lower()


class TestVerifyPlayerExercise:
    """Test verify_player_exercise() function."""

    def test_verify_exercise_success(
        self,
        session,
        sample_complete_player,
        sample_training_plan
    ):
        """Test successful exercise ownership verification."""
        # Given: Exercise belongs to player's plan
        exercise = sample_training_plan["exercises"][0]

        # When: Verify ownership
        result_exercise, result_plan = player_endpoint_service.verify_player_exercise(
            session,
            exercise.exercise_id,
            sample_complete_player.player_id
        )

        # Then: Returns exercise and plan
        assert result_exercise.exercise_id == exercise.exercise_id
        assert result_plan.player_id == sample_complete_player.player_id

    def test_verify_exercise_not_found(self, session, sample_complete_player):
        """Test exercise verification when exercise doesn't exist."""
        # Given: Random exercise ID
        random_exercise_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            player_endpoint_service.verify_player_exercise(
                session,
                random_exercise_id,
                sample_complete_player.player_id
            )

        assert "not found" in str(exc_info.value).lower()

    def test_verify_exercise_wrong_player(
        self,
        session,
        sample_training_plan
    ):
        """Test exercise verification with wrong player."""
        # Given: Exercise exists but belongs to different player's plan
        exercise = sample_training_plan["exercises"][0]
        different_player_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            player_endpoint_service.verify_player_exercise(
                session,
                exercise.exercise_id,
                different_player_id
            )

        assert "not part of your training plan" in str(exc_info.value).lower()


class TestGetPlayerDashboard:
    """Test get_player_dashboard() function."""

    def test_get_dashboard_success(
        self,
        session,
        sample_complete_player
    ):
        """Test successful dashboard retrieval."""
        # Given: Player exists

        # When: Get dashboard
        result = player_endpoint_service.get_player_dashboard(
            session,
            sample_complete_player.player_id
        )

        # Then: Returns correct structure
        assert "player" in result
        assert "attributes" in result
        assert "season_statistics" in result

        assert result["player"]["player_id"] == str(sample_complete_player.player_id)
        assert result["player"]["player_name"] == sample_complete_player.player_name

    def test_get_dashboard_with_age(self, session, sample_complete_player):
        """Test dashboard includes calculated age."""
        # Given: Player has birth_date

        # When: Get dashboard
        result = player_endpoint_service.get_player_dashboard(
            session,
            sample_complete_player.player_id
        )

        # Then: Age is calculated
        assert result["player"]["age"] is not None
        assert "years" in result["player"]["age"]

    def test_get_dashboard_with_statistics(
        self,
        session,
        sample_complete_player,
        sample_player_season_statistics
    ):
        """Test dashboard with season statistics."""
        # Given: Player has season statistics

        # When: Get dashboard
        result = player_endpoint_service.get_player_dashboard(
            session,
            sample_complete_player.player_id
        )

        # Then: Statistics are populated
        assert result["attributes"]["attacking_rating"] is not None
        assert result["season_statistics"]["general"]["matches_played"] > 0

    def test_get_dashboard_no_statistics(
        self,
        session,
        sample_complete_player
    ):
        """Test dashboard when player has no statistics."""
        # Given: Player exists but has no season statistics
        # (sample_player_season_statistics NOT included)

        # When: Get dashboard
        result = player_endpoint_service.get_player_dashboard(
            session,
            sample_complete_player.player_id
        )

        # Then: Returns with empty/default statistics (all 0)
        assert result["player"]["player_id"] == str(sample_complete_player.player_id)
        assert result["attributes"]["attacking_rating"] == 0
        assert result["season_statistics"]["general"]["matches_played"] == 0

    def test_get_dashboard_player_not_found(self, session):
        """Test dashboard with non-existent player."""
        # Given: Random player ID
        random_player_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            player_endpoint_service.get_player_dashboard(session, random_player_id)

        assert "not found" in str(exc_info.value).lower()


class TestGetPlayerMatches:
    """Test get_player_matches() function."""

    def test_get_matches_success(
        self,
        session,
        sample_complete_player,
        sample_match,
        sample_player_match_statistics
    ):
        """Test successful matches list retrieval."""
        # Given: Player has participated in matches

        # When: Get matches
        result = player_endpoint_service.get_player_matches(
            session,
            sample_complete_player.player_id
        )

        # Then: Returns matches list
        assert "total_count" in result
        assert "matches" in result
        assert result["total_count"] >= 1
        assert len(result["matches"]) >= 1

        # Verify match data
        match_item = result["matches"][0]
        assert "match_id" in match_item
        assert "opponent_name" in match_item
        assert "match_date" in match_item
        assert "result" in match_item

    def test_get_matches_pagination(
        self,
        session,
        sample_complete_player,
        sample_match,
        sample_player_match_statistics
    ):
        """Test matches pagination."""
        # Given: Player has matches

        # When: Get matches with limit
        result = player_endpoint_service.get_player_matches(
            session,
            sample_complete_player.player_id,
            limit=1,
            offset=0
        )

        # Then: Respects limit but returns total count
        assert len(result["matches"]) <= 1
        assert result["total_count"] >= 1

    def test_get_matches_empty(self, session, sample_incomplete_player):
        """Test matches list when player has no matches."""
        # Given: Player has no match statistics

        # When: Get matches
        result = player_endpoint_service.get_player_matches(
            session,
            sample_incomplete_player.player_id
        )

        # Then: Returns empty list
        assert result["total_count"] == 0
        assert result["matches"] == []


class TestGetPlayerMatchDetail:
    """Test get_player_match_detail() function."""

    def test_get_match_detail_success(
        self,
        session,
        sample_complete_player,
        sample_match,
        sample_player_match_statistics
    ):
        """Test successful match detail retrieval."""
        # Given: Player participated in match

        # When: Get match detail
        result = player_endpoint_service.get_player_match_detail(
            session,
            sample_complete_player.player_id,
            sample_match.match_id
        )

        # Then: Returns complete structure
        assert "match" in result
        assert "teams" in result
        assert "player_summary" in result
        assert "statistics" in result

        # Verify match info
        assert result["match"]["match_id"] == str(sample_match.match_id)

        # Verify player summary
        assert "goals" in result["player_summary"]
        assert "assists" in result["player_summary"]

    def test_get_match_detail_statistics_structure(
        self,
        session,
        sample_complete_player,
        sample_match,
        sample_player_match_statistics
    ):
        """Test match detail includes all statistics categories."""
        # Given: Player participated in match

        # When: Get match detail
        result = player_endpoint_service.get_player_match_detail(
            session,
            sample_complete_player.player_id,
            sample_match.match_id
        )

        # Then: Statistics have all categories
        stats = result["statistics"]
        assert "attacking" in stats
        assert "passing" in stats
        assert "defending" in stats

    def test_get_match_detail_not_participated(
        self,
        session,
        sample_complete_player,
        sample_match
    ):
        """Test match detail when player didn't participate."""
        # Given: Match exists but player has no statistics for it
        # (sample_player_match_statistics NOT included)

        # When/Then: Raises ValueError
        with pytest.raises(ValueError):
            player_endpoint_service.get_player_match_detail(
                session,
                sample_complete_player.player_id,
                sample_match.match_id
            )


class TestGetPlayerTrainingPlans:
    """Test get_player_training_plans() function."""

    def test_get_training_plans_success(
        self,
        session,
        sample_complete_player,
        sample_training_plan
    ):
        """Test successful training plans retrieval."""
        # Given: Player has training plans

        # When: Get training plans
        result = player_endpoint_service.get_player_training_plans(
            session,
            sample_complete_player.player_id
        )

        # Then: Returns plans list
        assert "training_plans" in result
        assert len(result["training_plans"]) >= 1

        # Verify plan data
        plan_item = result["training_plans"][0]
        assert "plan_id" in plan_item
        assert "plan_name" in plan_item
        assert "created_at" in plan_item
        assert "status" in plan_item

    def test_get_training_plans_empty(self, session, sample_incomplete_player):
        """Test training plans when player has none."""
        # Given: Player has no training plans

        # When: Get training plans
        result = player_endpoint_service.get_player_training_plans(
            session,
            sample_incomplete_player.player_id
        )

        # Then: Returns empty list
        assert result["training_plans"] == []


class TestGetPlayerTrainingPlanDetail:
    """Test get_player_training_plan_detail() function."""

    def test_get_plan_detail_success(
        self,
        session,
        sample_complete_player,
        sample_training_plan
    ):
        """Test successful plan detail retrieval."""
        # Given: Training plan exists
        plan = sample_training_plan["plan"]

        # When: Get plan detail
        result = player_endpoint_service.get_player_training_plan_detail(
            session,
            sample_complete_player.player_id,
            plan.plan_id
        )

        # Then: Returns complete structure
        assert "plan" in result
        assert "progress" in result
        assert "exercises" in result
        assert "coach_notes" in result

    def test_get_plan_detail_includes_exercises(
        self,
        session,
        sample_complete_player,
        sample_training_plan
    ):
        """Test plan detail includes exercises with completion status."""
        # Given: Plan has exercises
        plan = sample_training_plan["plan"]
        exercises = sample_training_plan["exercises"]

        # When: Get plan detail
        result = player_endpoint_service.get_player_training_plan_detail(
            session,
            sample_complete_player.player_id,
            plan.plan_id
        )

        # Then: Exercises include completion info
        assert len(result["exercises"]) == len(exercises)
        for ex in result["exercises"]:
            assert "completed" in ex
            assert "completed_at" in ex
            assert "exercise_order" in ex

    def test_get_plan_detail_progress_calculation(
        self,
        session,
        sample_complete_player,
        sample_training_plan
    ):
        """Test plan detail calculates progress correctly."""
        # Given: Plan has exercises (some completed)
        plan = sample_training_plan["plan"]
        exercises = sample_training_plan["exercises"]
        completed_count = sum(1 for e in exercises if e.completed)
        total_count = len(exercises)

        # When: Get plan detail
        result = player_endpoint_service.get_player_training_plan_detail(
            session,
            sample_complete_player.player_id,
            plan.plan_id
        )

        # Then: Progress is calculated correctly
        assert result["progress"]["total_exercises"] == total_count
        assert result["progress"]["completed_exercises"] == completed_count

    def test_get_plan_detail_wrong_player(
        self,
        session,
        sample_training_plan
    ):
        """Test plan detail with wrong player."""
        # Given: Plan belongs to different player
        plan = sample_training_plan["plan"]
        wrong_player_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError):
            player_endpoint_service.get_player_training_plan_detail(
                session,
                wrong_player_id,
                plan.plan_id
            )


class TestToggleExerciseCompletion:
    """Test toggle_exercise_completion() function."""

    def test_toggle_complete_exercise(
        self,
        session,
        sample_complete_player,
        sample_training_plan
    ):
        """Test marking exercise as complete."""
        # Given: Incomplete exercise
        exercises = sample_training_plan["exercises"]
        incomplete_exercise = next((e for e in exercises if not e.completed), None)

        # Skip if no incomplete exercise
        if incomplete_exercise is None:
            pytest.skip("No incomplete exercise in fixture")

        # When: Toggle to completed
        result = player_endpoint_service.toggle_exercise_completion(
            session,
            sample_complete_player.player_id,
            incomplete_exercise.exercise_id,
            completed=True
        )

        # Then: Exercise is marked complete
        assert result["completed"] is True
        assert result["completed_at"] is not None
        assert result["exercise_id"] == str(incomplete_exercise.exercise_id)

    def test_toggle_uncomplete_exercise(
        self,
        session,
        sample_complete_player,
        sample_training_plan
    ):
        """Test unmarking exercise as incomplete."""
        # Given: Complete exercise
        exercises = sample_training_plan["exercises"]
        complete_exercise = next((e for e in exercises if e.completed), None)

        # Skip if no complete exercise
        if complete_exercise is None:
            pytest.skip("No complete exercise in fixture")

        # When: Toggle to incomplete
        result = player_endpoint_service.toggle_exercise_completion(
            session,
            sample_complete_player.player_id,
            complete_exercise.exercise_id,
            completed=False
        )

        # Then: Exercise is marked incomplete
        assert result["completed"] is False
        assert result["completed_at"] is None

    def test_toggle_returns_plan_progress(
        self,
        session,
        sample_complete_player,
        sample_training_plan
    ):
        """Test toggle returns updated plan progress."""
        # Given: Exercise in plan
        exercise = sample_training_plan["exercises"][0]

        # When: Toggle exercise
        result = player_endpoint_service.toggle_exercise_completion(
            session,
            sample_complete_player.player_id,
            exercise.exercise_id,
            completed=not exercise.completed
        )

        # Then: Returns plan progress
        assert "plan_progress" in result
        assert "plan_id" in result["plan_progress"]
        assert "total_exercises" in result["plan_progress"]
        assert "completed_exercises" in result["plan_progress"]
        assert "progress_percentage" in result["plan_progress"]
        assert "plan_status" in result["plan_progress"]

    def test_toggle_updates_plan_status(
        self,
        session,
        sample_complete_player,
        sample_coach
    ):
        """Test plan status updates based on completion."""
        # Given: Create plan with single exercise
        plan = TrainingPlan(
            player_id=sample_complete_player.player_id,
            created_by=sample_coach.coach_id,
            plan_name="Test Plan",
            status="pending"
        )
        session.add(plan)
        session.flush()

        exercise = TrainingExercise(
            plan_id=plan.plan_id,
            exercise_name="Test Exercise",
            exercise_order=1,
            completed=False
        )
        session.add(exercise)
        session.flush()

        # When: Complete the only exercise
        result = player_endpoint_service.toggle_exercise_completion(
            session,
            sample_complete_player.player_id,
            exercise.exercise_id,
            completed=True
        )

        # Then: Plan status should be 'completed'
        assert result["plan_progress"]["plan_status"] == "completed"
        assert result["plan_progress"]["progress_percentage"] == 100

    def test_toggle_exercise_not_found(self, session, sample_complete_player):
        """Test toggle with non-existent exercise."""
        # Given: Random exercise ID
        random_exercise_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError):
            player_endpoint_service.toggle_exercise_completion(
                session,
                sample_complete_player.player_id,
                random_exercise_id,
                completed=True
            )

    def test_toggle_wrong_player(
        self,
        session,
        sample_training_plan
    ):
        """Test toggle with wrong player."""
        # Given: Exercise belongs to different player
        exercise = sample_training_plan["exercises"][0]
        wrong_player_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError):
            player_endpoint_service.toggle_exercise_completion(
                session,
                wrong_player_id,
                exercise.exercise_id,
                completed=True
            )


class TestGetPlayerProfile:
    """Test get_player_profile() function."""

    def test_get_profile_success(
        self,
        session,
        sample_complete_player
    ):
        """Test successful profile retrieval."""
        # Given: Complete player exists

        # When: Get profile
        result = player_endpoint_service.get_player_profile(
            session,
            sample_complete_player.player_id
        )

        # Then: Returns correct structure
        assert "player" in result
        assert "club" in result
        assert "season_summary" in result

    def test_get_profile_includes_email(
        self,
        session,
        sample_complete_player,
        sample_player_user
    ):
        """Test profile includes email from user account."""
        # Given: Linked player

        # When: Get profile
        result = player_endpoint_service.get_player_profile(
            session,
            sample_complete_player.player_id
        )

        # Then: Email is included from user
        assert result["player"]["email"] == sample_player_user.email

    def test_get_profile_includes_club(
        self,
        session,
        sample_complete_player,
        sample_club
    ):
        """Test profile includes club info."""
        # Given: Player in club

        # When: Get profile
        result = player_endpoint_service.get_player_profile(
            session,
            sample_complete_player.player_id
        )

        # Then: Club info is included
        assert result["club"]["club_name"] == sample_club.club_name

    def test_get_profile_with_season_summary(
        self,
        session,
        sample_complete_player,
        sample_player_season_statistics
    ):
        """Test profile includes season summary."""
        # Given: Player has season statistics

        # When: Get profile
        result = player_endpoint_service.get_player_profile(
            session,
            sample_complete_player.player_id
        )

        # Then: Season summary is populated
        assert result["season_summary"]["matches_played"] > 0
        assert "goals" in result["season_summary"]
        assert "assists" in result["season_summary"]

    def test_get_profile_no_statistics(
        self,
        session,
        sample_complete_player
    ):
        """Test profile when player has no statistics."""
        # Given: Player has no season statistics
        # (sample_player_season_statistics NOT included)

        # When: Get profile
        result = player_endpoint_service.get_player_profile(
            session,
            sample_complete_player.player_id
        )

        # Then: Returns with zero statistics
        assert result["season_summary"]["matches_played"] == 0
        assert result["season_summary"]["goals"] == 0
        assert result["season_summary"]["assists"] == 0

    def test_get_profile_player_not_found(self, session):
        """Test profile with non-existent player."""
        # Given: Random player ID
        random_player_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            player_endpoint_service.get_player_profile(session, random_player_id)

        assert "not found" in str(exc_info.value).lower()
