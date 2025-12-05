"""
Tests for coach service module.

Tests all coach service functions following Given-When-Then pattern:
- Helper functions (calculate_age, _build_stat_comparison, etc.)
- Ownership verification functions
- Dashboard and profile services
- Match services
- Player services
- Training plan services

Each test follows the pattern:
    # Given: Setup test data
    # When: Call service function
    # Then: Assert results and verify database state
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from app.services import coach_service
from app.models.user import User
from app.models.coach import Coach
from app.models.club import Club
from app.models.player import Player
from app.models.training_plan import TrainingPlan
from app.models.training_exercise import TrainingExercise


# ============================================================================
# HELPER FUNCTIONS TESTS
# ============================================================================

class TestHelperFunctions:
    """Test helper functions (no database operations)."""

    def test_calculate_age_valid_birth_date(self):
        """Test age calculation with valid birth date."""
        # Given: A birth date 25 years ago
        birth_date = date(2000, 1, 15)

        # When: Calculate age
        result = coach_service.calculate_age(birth_date)

        # Then: Returns age string
        # Note: Exact age depends on current date, but format should be correct
        assert result is not None
        assert "years" in result
        assert result.split()[0].isdigit()

    def test_calculate_age_birthday_not_yet_this_year(self):
        """Test age calculation when birthday hasn't occurred yet this year."""
        # Given: A birth date in the future of this year
        today = date.today()
        # Birth date: same year as today but in future month
        if today.month < 12:
            birth_date = date(today.year - 25, today.month + 1, 1)
        else:
            birth_date = date(today.year - 25, 1, 1)

        # When: Calculate age
        result = coach_service.calculate_age(birth_date)

        # Then: Age should account for birthday not yet occurring
        assert result is not None
        assert "years" in result

    def test_calculate_age_none_birth_date(self):
        """Test age calculation with None birth date."""
        # Given: None birth date
        birth_date = None

        # When: Calculate age
        result = coach_service.calculate_age(birth_date)

        # Then: Returns None
        assert result is None

    def test_build_stat_comparison_valid_values(self):
        """Test building stat comparison with valid values."""
        # Given: Two stat values
        our_val = 52.5
        opp_val = 47.5

        # When: Build comparison
        result = coach_service._build_stat_comparison(our_val, opp_val)

        # Then: Returns correct structure
        assert result == {"our_team": 52.5, "opponent": 47.5}

    def test_build_stat_comparison_none_values(self):
        """Test building stat comparison with None values."""
        # Given: None values
        our_val = None
        opp_val = None

        # When: Build comparison
        result = coach_service._build_stat_comparison(our_val, opp_val)

        # Then: Returns zeros
        assert result == {"our_team": 0, "opponent": 0}

    def test_build_stat_comparison_mixed_values(self):
        """Test building stat comparison with mixed None and valid values."""
        # Given: One None and one valid
        our_val = 10
        opp_val = None

        # When: Build comparison
        result = coach_service._build_stat_comparison(our_val, opp_val)

        # Then: None becomes 0
        assert result == {"our_team": 10, "opponent": 0}

    def test_calculate_win_rate_valid(self):
        """Test win rate calculation with valid values."""
        # Given: 5 wins out of 10 matches
        wins = 5
        matches_played = 10

        # When: Calculate win rate
        result = coach_service._calculate_win_rate(wins, matches_played)

        # Then: Returns 50%
        assert result == 50

    def test_calculate_win_rate_zero_matches(self):
        """Test win rate calculation with zero matches."""
        # Given: 0 matches played
        wins = 0
        matches_played = 0

        # When: Calculate win rate
        result = coach_service._calculate_win_rate(wins, matches_played)

        # Then: Returns None
        assert result is None

    def test_calculate_win_rate_perfect_record(self):
        """Test win rate calculation with 100% wins."""
        # Given: All wins
        wins = 10
        matches_played = 10

        # When: Calculate win rate
        result = coach_service._calculate_win_rate(wins, matches_played)

        # Then: Returns 100%
        assert result == 100

    def test_calculate_training_progress_all_completed(self):
        """Test training progress with all exercises completed."""
        # Given: Exercises all completed
        exercises = [
            TrainingExercise(exercise_name="Ex1", exercise_order=1, completed=True),
            TrainingExercise(exercise_name="Ex2", exercise_order=2, completed=True),
            TrainingExercise(exercise_name="Ex3", exercise_order=3, completed=True)
        ]

        # When: Calculate progress
        result = coach_service._calculate_training_progress(exercises)

        # Then: Returns 100%
        assert result["percentage"] == 100
        assert result["completed_exercises"] == 3
        assert result["total_exercises"] == 3

    def test_calculate_training_progress_partial_completed(self):
        """Test training progress with some exercises completed."""
        # Given: 2 out of 4 completed
        exercises = [
            TrainingExercise(exercise_name="Ex1", exercise_order=1, completed=True),
            TrainingExercise(exercise_name="Ex2", exercise_order=2, completed=False),
            TrainingExercise(exercise_name="Ex3", exercise_order=3, completed=True),
            TrainingExercise(exercise_name="Ex4", exercise_order=4, completed=False)
        ]

        # When: Calculate progress
        result = coach_service._calculate_training_progress(exercises)

        # Then: Returns 50%
        assert result["percentage"] == 50
        assert result["completed_exercises"] == 2
        assert result["total_exercises"] == 4

    def test_calculate_training_progress_empty_list(self):
        """Test training progress with no exercises."""
        # Given: Empty exercises list
        exercises = []

        # When: Calculate progress
        result = coach_service._calculate_training_progress(exercises)

        # Then: Returns 0%
        assert result["percentage"] == 0
        assert result["completed_exercises"] == 0
        assert result["total_exercises"] == 0


# ============================================================================
# OWNERSHIP VERIFICATION TESTS
# ============================================================================

class TestGetCoachClub:
    """Test get_coach_club() function."""

    def test_get_coach_club_success(self, session, sample_user, sample_coach, sample_club):
        """Test successful retrieval of coach's club."""
        # Given: Coach with club exists in database
        # (provided by fixtures)

        # When: Get coach club
        result = coach_service.get_coach_club(session, sample_user.user_id)

        # Then: Returns the club
        assert result.club_id == sample_club.club_id
        assert result.club_name == sample_club.club_name

    def test_get_coach_club_coach_not_found(self, session):
        """Test get_coach_club with non-existent coach."""
        # Given: Random user ID that doesn't exist
        random_user_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.get_coach_club(session, random_user_id)

        assert "Coach not found" in str(exc_info.value)

    def test_get_coach_club_no_club(self, session, sample_user, sample_coach):
        """Test get_coach_club when coach has no club."""
        # Given: Coach exists but has no club
        # Delete the club created by fixture
        session.query(Club).filter(Club.coach_id == sample_coach.coach_id).delete()
        session.commit()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.get_coach_club(session, sample_user.user_id)

        assert "Coach has no club" in str(exc_info.value)


class TestVerifyMatchOwnership:
    """Test verify_match_ownership() function."""

    def test_verify_match_ownership_success(self, session, sample_club, sample_match):
        """Test successful match ownership verification."""
        # Given: Match belongs to club
        # (provided by fixtures)

        # When: Verify ownership
        result = coach_service.verify_match_ownership(
            session,
            sample_match.match_id,
            sample_club.club_id
        )

        # Then: Returns the match
        assert result.match_id == sample_match.match_id
        assert result.club_id == sample_club.club_id

    def test_verify_match_ownership_not_found(self, session, sample_club):
        """Test verify_match_ownership with non-existent match."""
        # Given: Random match ID
        random_match_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.verify_match_ownership(session, random_match_id, sample_club.club_id)

        assert "Match not found" in str(exc_info.value)

    def test_verify_match_ownership_wrong_club(self, session, sample_match):
        """Test verify_match_ownership with match from different club."""
        # Given: Match exists but belongs to different club
        different_club_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.verify_match_ownership(session, sample_match.match_id, different_club_id)

        assert "does not belong to your club" in str(exc_info.value)


class TestVerifyPlayerOwnership:
    """Test verify_player_ownership() function."""

    def test_verify_player_ownership_success(self, session, sample_club, sample_complete_player):
        """Test successful player ownership verification."""
        # Given: Player belongs to club
        # (provided by fixtures)

        # When: Verify ownership
        result = coach_service.verify_player_ownership(
            session,
            sample_complete_player.player_id,
            sample_club.club_id
        )

        # Then: Returns the player
        assert result.player_id == sample_complete_player.player_id
        assert result.club_id == sample_club.club_id

    def test_verify_player_ownership_not_found(self, session, sample_club):
        """Test verify_player_ownership with non-existent player."""
        # Given: Random player ID
        random_player_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.verify_player_ownership(session, random_player_id, sample_club.club_id)

        assert "Player not found" in str(exc_info.value)

    def test_verify_player_ownership_wrong_club(self, session, sample_complete_player):
        """Test verify_player_ownership with player from different club."""
        # Given: Player exists but belongs to different club
        different_club_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.verify_player_ownership(
                session,
                sample_complete_player.player_id,
                different_club_id
            )

        assert "does not belong to your club" in str(exc_info.value)


class TestVerifyTrainingPlanOwnership:
    """Test verify_training_plan_ownership() function."""

    def test_verify_training_plan_ownership_success(
        self,
        session,
        sample_coach,
        sample_training_plan
    ):
        """Test successful training plan ownership verification."""
        # Given: Training plan belongs to coach's club
        plan = sample_training_plan["plan"]

        # When: Verify ownership
        result = coach_service.verify_training_plan_ownership(
            session,
            plan.plan_id,
            sample_coach.coach_id
        )

        # Then: Returns the plan
        assert result.plan_id == plan.plan_id

    def test_verify_training_plan_ownership_not_found(self, session, sample_coach):
        """Test verify_training_plan_ownership with non-existent plan."""
        # Given: Random plan ID
        random_plan_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.verify_training_plan_ownership(
                session,
                random_plan_id,
                sample_coach.coach_id
            )

        assert "Training plan not found" in str(exc_info.value)

    def test_verify_training_plan_ownership_wrong_club(self, session, sample_training_plan):
        """Test verify_training_plan_ownership with plan from different coach."""
        # Given: Plan exists but belongs to different coach
        plan = sample_training_plan["plan"]
        different_coach_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.verify_training_plan_ownership(
                session,
                plan.plan_id,
                different_coach_id
            )

        assert "does not belong to your club" in str(exc_info.value)


# ============================================================================
# PROFILE & DASHBOARD TESTS
# ============================================================================

class TestGetCoachProfile:
    """Test get_coach_profile() function."""

    def test_get_profile_success(self, session, sample_user, sample_coach, sample_club):
        """Test successful profile retrieval."""
        # Given: Coach with club exists
        # (provided by fixtures)

        # When: Get profile
        result = coach_service.get_coach_profile(session, sample_user.user_id)

        # Then: Returns correct structure
        assert "coach" in result
        assert "club" in result
        assert "club_stats" in result

        # Verify coach data
        assert result["coach"]["full_name"] == sample_user.full_name
        assert result["coach"]["email"] == sample_user.email
        assert result["coach"]["gender"] == sample_coach.gender
        assert result["coach"]["birth_date"] == sample_coach.birth_date

        # Verify club data
        assert result["club"]["club_id"] == str(sample_club.club_id)
        assert result["club"]["club_name"] == sample_club.club_name

    def test_get_profile_with_statistics(
        self,
        session,
        sample_user,
        sample_club,
        sample_club_season_statistics
    ):
        """Test profile retrieval with club statistics."""
        # Given: Club has season statistics
        # (provided by fixtures)

        # When: Get profile
        result = coach_service.get_coach_profile(session, sample_user.user_id)

        # Then: Club stats include data from statistics
        assert result["club_stats"]["total_matches"] == sample_club_season_statistics.matches_played
        assert result["club_stats"]["win_rate_percentage"] is not None

    def test_get_profile_no_statistics(self, session, sample_user, sample_club):
        """Test profile retrieval with no statistics."""
        # Given: Club has no season statistics
        # (no sample_club_season_statistics fixture used)

        # When: Get profile
        result = coach_service.get_coach_profile(session, sample_user.user_id)

        # Then: Stats show zeros
        assert result["club_stats"]["total_matches"] == 0
        assert result["club_stats"]["win_rate_percentage"] is None

    def test_get_profile_coach_not_found(self, session):
        """Test get_profile with non-existent coach."""
        # Given: Random user ID
        random_user_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.get_coach_profile(session, random_user_id)

        assert "Coach or club not found" in str(exc_info.value)


class TestGetDashboardData:
    """Test get_dashboard_data() function."""

    def test_get_dashboard_success(self, session, sample_user, sample_club):
        """Test successful dashboard data retrieval."""
        # Given: Coach with club exists
        # (provided by fixtures)

        # When: Get dashboard
        result = coach_service.get_dashboard_data(session, sample_user.user_id)

        # Then: Returns correct structure
        assert "coach" in result
        assert "club" in result
        assert "season_record" in result
        assert "team_form" in result
        assert "matches" in result
        assert "statistics" in result

    def test_get_dashboard_with_statistics(
        self,
        session,
        sample_user,
        sample_club,
        sample_club_season_statistics
    ):
        """Test dashboard with club statistics."""
        # Given: Club has season statistics
        # (provided by fixtures)

        # When: Get dashboard
        result = coach_service.get_dashboard_data(session, sample_user.user_id)

        # Then: Statistics are populated
        assert result["season_record"]["wins"] == sample_club_season_statistics.wins
        assert result["season_record"]["draws"] == sample_club_season_statistics.draws
        assert result["season_record"]["losses"] == sample_club_season_statistics.losses
        assert result["team_form"] == sample_club_season_statistics.team_form

        # Verify attacking stats
        assert result["statistics"]["attacking"]["avg_goals_per_match"] is not None

        # Verify defending stats
        assert result["statistics"]["defending"]["total_clean_sheets"] == sample_club_season_statistics.total_clean_sheets

    def test_get_dashboard_with_matches(
        self,
        session,
        sample_user,
        sample_club,
        sample_match,
        sample_club_season_statistics
    ):
        """Test dashboard with matches."""
        # Given: Club has matches and statistics
        # (provided by fixtures)

        # When: Get dashboard
        result = coach_service.get_dashboard_data(session, sample_user.user_id)

        # Then: Matches are included
        assert result["matches"]["total_count"] >= 1
        assert len(result["matches"]["matches"]) >= 1

        # Verify match data
        match_data = result["matches"]["matches"][0]
        assert match_data["match_id"] == str(sample_match.match_id)
        assert match_data["opponent_name"] == sample_match.opponent_name

    def test_get_dashboard_with_pagination(
        self,
        session,
        sample_user,
        sample_club,
        sample_opponent_club
    ):
        """Test dashboard matches pagination."""
        # Given: Multiple matches
        from app.models.match import Match
        for i in range(5):
            match = Match(
                club_id=sample_club.club_id,
                opponent_club_id=sample_opponent_club.opponent_club_id,
                opponent_name="Test Opponent",
                match_date=date(2024, 1, i + 1),
                our_score=1,
                opponent_score=1,
                result="D"
            )
            session.add(match)
        session.commit()

        # When: Get dashboard with limit
        result = coach_service.get_dashboard_data(
            session,
            sample_user.user_id,
            matches_limit=3,
            matches_offset=0
        )

        # Then: Returns limited matches
        assert len(result["matches"]["matches"]) <= 3

    def test_get_dashboard_no_statistics(self, session, sample_user, sample_club):
        """Test dashboard with no statistics."""
        # Given: Club has no statistics
        # (no sample_club_season_statistics fixture used)

        # When: Get dashboard
        result = coach_service.get_dashboard_data(session, sample_user.user_id)

        # Then: Returns default empty structure
        assert result["season_record"]["wins"] == 0
        assert result["statistics"]["season_summary"]["matches_played"] == 0
        assert result["statistics"]["attacking"]["avg_goals_per_match"] is None

    def test_get_dashboard_coach_not_found(self, session):
        """Test get_dashboard with non-existent coach."""
        # Given: Random user ID
        random_user_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.get_dashboard_data(session, random_user_id)

        assert "Coach or club not found" in str(exc_info.value)


# ============================================================================
# MATCH SERVICES TESTS
# ============================================================================

class TestGetMatchDetail:
    """Test get_match_detail() function."""

    def test_get_match_detail_success(self, session, sample_club, sample_match):
        """Test successful match detail retrieval."""
        # Given: Match exists
        # (provided by fixtures)

        # When: Get match detail
        result = coach_service.get_match_detail(
            session,
            sample_match.match_id,
            sample_club.club_id
        )

        # Then: Returns correct structure
        assert "match" in result
        assert "teams" in result
        assert "summary" in result
        assert "statistics" in result
        assert "lineup" in result

        # Verify match data
        assert result["match"]["match_id"] == str(sample_match.match_id)
        assert result["match"]["our_score"] == sample_match.our_score
        assert result["match"]["opponent_score"] == sample_match.opponent_score

    def test_get_match_detail_with_goals(self, session, sample_club, sample_match, sample_goals):
        """Test match detail with goals."""
        # Given: Match has goals
        # (provided by fixtures)

        # When: Get match detail
        result = coach_service.get_match_detail(
            session,
            sample_match.match_id,
            sample_club.club_id
        )

        # Then: Goals are included
        assert len(result["summary"]["goal_scorers"]) == len(sample_goals)

        # Verify goal data
        first_goal = result["summary"]["goal_scorers"][0]
        assert "scorer_name" in first_goal
        assert "minute" in first_goal
        assert "is_our_goal" in first_goal

    def test_get_match_detail_with_statistics(
        self,
        session,
        sample_club,
        sample_match,
        sample_match_statistics
    ):
        """Test match detail with statistics."""
        # Given: Match has statistics
        our_stats = sample_match_statistics["our_team"]
        opp_stats = sample_match_statistics["opponent_team"]

        # When: Get match detail
        result = coach_service.get_match_detail(
            session,
            sample_match.match_id,
            sample_club.club_id
        )

        # Then: Statistics are populated
        stats = result["statistics"]
        assert stats["match_overview"]["ball_possession"]["our_team"] > 0
        assert stats["attacking"]["total_shots"]["our_team"] == our_stats.total_shots

    def test_get_match_detail_with_lineups(
        self,
        session,
        sample_club,
        sample_match,
        sample_lineups
    ):
        """Test match detail with lineups."""
        # Given: Match has lineups
        # (provided by fixtures)

        # When: Get match detail
        result = coach_service.get_match_detail(
            session,
            sample_match.match_id,
            sample_club.club_id
        )

        # Then: Lineups are included
        assert len(result["lineup"]["our_team"]) > 0
        assert len(result["lineup"]["opponent_team"]) > 0

    def test_get_match_detail_no_statistics(self, session, sample_club, sample_match):
        """Test match detail with no statistics."""
        # Given: Match exists but has no statistics
        # (no sample_match_statistics fixture used)

        # When: Get match detail
        result = coach_service.get_match_detail(
            session,
            sample_match.match_id,
            sample_club.club_id
        )

        # Then: Statistics show zeros
        assert result["statistics"]["match_overview"]["ball_possession"]["our_team"] == 0

    def test_get_match_detail_not_found(self, session, sample_club):
        """Test get_match_detail with non-existent match."""
        # Given: Random match ID
        random_match_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.get_match_detail(session, random_match_id, sample_club.club_id)

        assert "Match not found" in str(exc_info.value)

    def test_get_match_detail_wrong_club(self, session, sample_match):
        """Test get_match_detail with match from different club."""
        # Given: Match exists but belongs to different club
        different_club_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.get_match_detail(session, sample_match.match_id, different_club_id)

        assert "does not belong to your club" in str(exc_info.value)


# ============================================================================
# PLAYER SERVICES TESTS
# ============================================================================

class TestGetPlayersList:
    """Test get_players_list() function."""

    def test_get_players_list_success(self, session, sample_club, sample_complete_player):
        """Test successful players list retrieval."""
        # Given: Club has players
        # (provided by fixtures)

        # When: Get players list
        result = coach_service.get_players_list(session, sample_club.club_id)

        # Then: Returns correct structure
        assert "summary" in result
        assert "players" in result

        # Verify players are included
        assert len(result["players"]) >= 1

    def test_get_players_list_with_counts(
        self,
        session,
        sample_club,
        sample_complete_player,
        sample_incomplete_player
    ):
        """Test players list with linked and unlinked counts."""
        # Given: Club has both linked and unlinked players
        # (provided by fixtures)

        # When: Get players list
        result = coach_service.get_players_list(session, sample_club.club_id)

        # Then: Summary includes correct counts
        assert result["summary"]["total_players"] >= 2
        assert result["summary"]["joined"] >= 1  # complete_player is linked
        assert result["summary"]["pending"] >= 1  # incomplete_player is not linked

    def test_get_players_list_empty_club(self, session, sample_coach):
        """Test players list for club with no players."""
        # Given: Club with no players
        club = Club(
            coach_id=sample_coach.coach_id,
            club_name="Empty Club",
            country="England",
            age_group="U16"
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        # When: Get players list
        result = coach_service.get_players_list(session, club.club_id)

        # Then: Returns empty lists
        assert result["summary"]["total_players"] == 0
        assert result["summary"]["joined"] == 0
        assert result["summary"]["pending"] == 0
        assert len(result["players"]) == 0

    def test_get_players_list_ordered_by_jersey(self, session, sample_club):
        """Test players list is ordered by jersey number."""
        # Given: Multiple players with different jersey numbers
        for jersey_num in [10, 5, 15, 3]:
            player = Player(
                club_id=sample_club.club_id,
                player_name=f"Player {jersey_num}",
                jersey_number=jersey_num,
                position="Forward",
                invite_code=f"TEST-{jersey_num}",
                is_linked=False
            )
            session.add(player)
        session.commit()

        # When: Get players list
        result = coach_service.get_players_list(session, sample_club.club_id)

        # Then: Players are ordered by jersey number
        jersey_numbers = [p["jersey_number"] for p in result["players"]]
        assert jersey_numbers == sorted(jersey_numbers)


class TestGetPlayerDetail:
    """Test get_player_detail() function."""

    def test_get_player_detail_success(
        self,
        session,
        sample_club,
        sample_complete_player
    ):
        """Test successful player detail retrieval."""
        # Given: Player exists
        # (provided by fixtures)

        # When: Get player detail
        result = coach_service.get_player_detail(
            session,
            sample_complete_player.player_id,
            sample_club.club_id
        )

        # Then: Returns correct structure
        assert "player" in result
        assert "attributes" in result
        assert "season_statistics" in result
        assert "matches" in result
        assert "training_plans" in result

        # Verify player data
        assert result["player"]["player_id"] == str(sample_complete_player.player_id)
        assert result["player"]["player_name"] == sample_complete_player.player_name

    def test_get_player_detail_with_age(self, session, sample_club, sample_complete_player):
        """Test player detail includes age calculation."""
        # Given: Player has birth_date
        # (sample_complete_player has birth_date)

        # When: Get player detail
        result = coach_service.get_player_detail(
            session,
            sample_complete_player.player_id,
            sample_club.club_id
        )

        # Then: Age is calculated
        assert result["player"]["age"] is not None
        assert "years" in result["player"]["age"]

    def test_get_player_detail_invite_code_unlinked(
        self,
        session,
        sample_club,
        sample_incomplete_player
    ):
        """Test player detail includes invite_code for unlinked players."""
        # Given: Unlinked player
        # (sample_incomplete_player has is_linked=False)

        # When: Get player detail
        result = coach_service.get_player_detail(
            session,
            sample_incomplete_player.player_id,
            sample_club.club_id
        )

        # Then: Invite code is included
        assert result["invite_code"] is not None
        assert result["invite_code"] == sample_incomplete_player.invite_code

    def test_get_player_detail_no_invite_code_linked(
        self,
        session,
        sample_club,
        sample_complete_player
    ):
        """Test player detail excludes invite_code for linked players."""
        # Given: Linked player
        # (sample_complete_player has is_linked=True)

        # When: Get player detail
        result = coach_service.get_player_detail(
            session,
            sample_complete_player.player_id,
            sample_club.club_id
        )

        # Then: Invite code is None
        assert result["invite_code"] is None

    def test_get_player_detail_with_statistics(
        self,
        session,
        sample_club,
        sample_complete_player,
        sample_player_season_statistics
    ):
        """Test player detail with season statistics."""
        # Given: Player has season statistics
        # (provided by fixtures)

        # When: Get player detail
        result = coach_service.get_player_detail(
            session,
            sample_complete_player.player_id,
            sample_club.club_id
        )

        # Then: Statistics are populated
        assert result["attributes"]["attacking_rating"] == sample_player_season_statistics.attacking_rating
        assert result["season_statistics"]["general"]["matches_played"] == sample_player_season_statistics.matches_played
        assert result["season_statistics"]["attacking"]["goals"] == sample_player_season_statistics.goals

    def test_get_player_detail_no_statistics(
        self,
        session,
        sample_club,
        sample_incomplete_player
    ):
        """Test player detail with no statistics."""
        # Given: Player has no statistics
        # (sample_incomplete_player has no season stats)

        # When: Get player detail
        result = coach_service.get_player_detail(
            session,
            sample_incomplete_player.player_id,
            sample_club.club_id
        )

        # Then: Statistics show defaults
        assert result["attributes"]["attacking_rating"] is None
        assert result["season_statistics"]["general"]["matches_played"] == 0

    def test_get_player_detail_with_matches(
        self,
        session,
        sample_club,
        sample_complete_player,
        sample_match,
        sample_player_match_statistics
    ):
        """Test player detail includes matches."""
        # Given: Player has match statistics
        # (provided by fixtures)

        # When: Get player detail
        result = coach_service.get_player_detail(
            session,
            sample_complete_player.player_id,
            sample_club.club_id
        )

        # Then: Matches are included
        assert result["matches"]["total_count"] >= 1

    def test_get_player_detail_with_training_plans(
        self,
        session,
        sample_club,
        sample_complete_player,
        sample_training_plan
    ):
        """Test player detail includes training plans."""
        # Given: Player has training plans
        # (provided by fixtures)

        # When: Get player detail
        result = coach_service.get_player_detail(
            session,
            sample_complete_player.player_id,
            sample_club.club_id
        )

        # Then: Training plans are included
        assert len(result["training_plans"]) >= 1

    def test_get_player_detail_not_found(self, session, sample_club):
        """Test get_player_detail with non-existent player."""
        # Given: Random player ID
        random_player_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.get_player_detail(session, random_player_id, sample_club.club_id)

        assert "Player not found" in str(exc_info.value)

    def test_get_player_detail_wrong_club(self, session, sample_complete_player):
        """Test get_player_detail with player from different club."""
        # Given: Player exists but belongs to different club
        different_club_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.get_player_detail(
                session,
                sample_complete_player.player_id,
                different_club_id
            )

        assert "does not belong to your club" in str(exc_info.value)


class TestGetPlayerMatchStats:
    """Test get_player_match_stats() function."""

    def test_get_player_match_stats_success(
        self,
        session,
        sample_club,
        sample_complete_player,
        sample_match,
        sample_player_match_statistics
    ):
        """Test successful player match stats retrieval."""
        # Given: Player has match statistics
        # (provided by fixtures)

        # When: Get player match stats
        result = coach_service.get_player_match_stats(
            session,
            sample_complete_player.player_id,
            sample_match.match_id,
            sample_club.club_id
        )

        # Then: Returns correct structure
        assert "match" in result
        assert "teams" in result
        assert "player_summary" in result
        assert "statistics" in result

    def test_get_player_match_stats_complete_data(
        self,
        session,
        sample_club,
        sample_complete_player,
        sample_match,
        sample_player_match_statistics
    ):
        """Test player match stats with complete data."""
        # Given: Full match statistics exist
        # (provided by fixtures)

        # When: Get player match stats
        result = coach_service.get_player_match_stats(
            session,
            sample_complete_player.player_id,
            sample_match.match_id,
            sample_club.club_id
        )

        # Then: All statistics are present
        assert result["player_summary"]["goals"] == sample_player_match_statistics.goals
        assert result["statistics"]["attacking"]["goals"] == sample_player_match_statistics.goals
        assert result["statistics"]["passing"]["total_passes"] == sample_player_match_statistics.total_passes

    def test_get_player_match_stats_player_not_found(self, session, sample_club, sample_match):
        """Test get_player_match_stats with non-existent player."""
        # Given: Random player ID
        random_player_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.get_player_match_stats(
                session,
                random_player_id,
                sample_match.match_id,
                sample_club.club_id
            )

        assert "Player not found" in str(exc_info.value)

    def test_get_player_match_stats_match_not_found(
        self,
        session,
        sample_club,
        sample_complete_player
    ):
        """Test get_player_match_stats with non-existent match."""
        # Given: Random match ID
        random_match_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.get_player_match_stats(
                session,
                sample_complete_player.player_id,
                random_match_id,
                sample_club.club_id
            )

        assert "Match not found" in str(exc_info.value)

    def test_get_player_match_stats_stats_not_found(
        self,
        session,
        sample_club,
        sample_complete_player,
        sample_match
    ):
        """Test get_player_match_stats when player stats don't exist for match."""
        # Given: Match exists but player has no stats for it
        # (no sample_player_match_statistics fixture used)

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.get_player_match_stats(
                session,
                sample_complete_player.player_id,
                sample_match.match_id,
                sample_club.club_id
            )

        assert "Player statistics not found" in str(exc_info.value)


# ============================================================================
# TRAINING PLAN SERVICES TESTS
# ============================================================================

class TestGenerateAITrainingPlan:
    """Test generate_ai_training_plan() function."""

    def test_generate_ai_plan_success(
        self,
        session,
        sample_club,
        sample_complete_player
    ):
        """Test successful AI plan generation."""
        # Given: Player exists
        # (provided by fixtures)

        # When: Generate AI plan
        result = coach_service.generate_ai_training_plan(
            session,
            sample_complete_player.player_id,
            sample_club.club_id
        )

        # Then: Returns correct structure
        assert "player_name" in result
        assert "plan_name" in result
        assert "exercises" in result
        assert len(result["exercises"]) > 0

    def test_generate_ai_plan_returns_stub_data(
        self,
        session,
        sample_club,
        sample_complete_player
    ):
        """Test AI plan generation returns hardcoded stub."""
        # Given: Player exists
        # (provided by fixtures)

        # When: Generate AI plan
        result = coach_service.generate_ai_training_plan(
            session,
            sample_complete_player.player_id,
            sample_club.club_id
        )

        # Then: Returns stub data
        assert result["player_name"] == sample_complete_player.player_name
        assert "AI-Generated" in result["plan_name"]
        assert result["duration"] == "2 weeks"
        assert len(result["exercises"]) == 3

    def test_generate_ai_plan_player_not_found(self, session, sample_club):
        """Test generate_ai_plan with non-existent player."""
        # Given: Random player ID
        random_player_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.generate_ai_training_plan(
                session,
                random_player_id,
                sample_club.club_id
            )

        assert "Player not found" in str(exc_info.value)

    def test_generate_ai_plan_wrong_club(self, session, sample_complete_player):
        """Test generate_ai_plan with player from different club."""
        # Given: Player exists but belongs to different club
        different_club_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.generate_ai_training_plan(
                session,
                sample_complete_player.player_id,
                different_club_id
            )

        assert "does not belong to your club" in str(exc_info.value)


class TestCreateTrainingPlan:
    """Test create_training_plan() function."""

    def test_create_training_plan_success(
        self,
        session,
        sample_coach,
        sample_complete_player
    ):
        """Test successful training plan creation."""
        # Given: Plan data
        plan_data = {
            "plan_name": "Test Plan",
            "duration": "2 weeks",
            "coach_notes": "Test notes",
            "exercises": []
        }

        # When: Create training plan
        result = coach_service.create_training_plan(
            session,
            sample_complete_player.player_id,
            sample_coach.coach_id,
            plan_data
        )

        # Then: Plan is created
        assert "plan_id" in result
        assert result["plan_name"] == "Test Plan"
        assert result["status"] == "pending"

        # Verify database state
        plan = session.query(TrainingPlan).filter(
            TrainingPlan.plan_id == result["plan_id"]
        ).first()
        assert plan is not None
        assert plan.plan_name == "Test Plan"

    def test_create_training_plan_with_exercises(
        self,
        session,
        sample_coach,
        sample_complete_player
    ):
        """Test training plan creation with exercises."""
        # Given: Plan data with exercises
        plan_data = {
            "plan_name": "Plan with Exercises",
            "duration": "1 week",
            "exercises": [
                {
                    "exercise_name": "Exercise 1",
                    "description": "Description 1",
                    "sets": "3",
                    "reps": "10",
                    "duration_minutes": "15",
                    "exercise_order": 1
                },
                {
                    "exercise_name": "Exercise 2",
                    "description": "Description 2",
                    "sets": "4",
                    "reps": "8",
                    "duration_minutes": "20",
                    "exercise_order": 2
                }
            ]
        }

        # When: Create training plan
        result = coach_service.create_training_plan(
            session,
            sample_complete_player.player_id,
            sample_coach.coach_id,
            plan_data
        )

        # Then: Exercises are created
        assert result["exercise_count"] == 2

        # Verify database state
        session.commit()  # Commit to persist
        exercises = session.query(TrainingExercise).filter(
            TrainingExercise.plan_id == result["plan_id"]
        ).all()
        assert len(exercises) == 2

    def test_create_training_plan_flush_not_commit(
        self,
        session,
        sample_coach,
        sample_complete_player
    ):
        """Test that create_training_plan flushes but doesn't commit."""
        # Given: Plan data
        plan_data = {
            "plan_name": "Test Flush",
            "exercises": []
        }

        # When: Create training plan
        result = coach_service.create_training_plan(
            session,
            sample_complete_player.player_id,
            sample_coach.coach_id,
            plan_data
        )

        # Rollback to test flush behavior
        session.rollback()

        # Then: Changes are rolled back
        plan = session.query(TrainingPlan).filter(
            TrainingPlan.plan_id == result["plan_id"]
        ).first()
        assert plan is None

    def test_create_training_plan_player_not_found(self, session, sample_coach, sample_club):
        """Test create_training_plan with non-existent player."""
        # Given: Coach has club but random player ID doesn't exist
        random_player_id = uuid4()
        plan_data = {"plan_name": "Test", "exercises": []}

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.create_training_plan(
                session,
                random_player_id,
                sample_coach.coach_id,
                plan_data
            )

        assert "Player not found" in str(exc_info.value)

    def test_create_training_plan_coach_no_club(self, session, sample_player_user):
        """Test create_training_plan when coach has no club."""
        # Given: Coach without club
        coach = Coach(
            user_id=sample_player_user.user_id,
            birth_date=date(1990, 1, 1),
            gender="male"
        )
        session.add(coach)
        session.commit()
        session.refresh(coach)

        plan_data = {"plan_name": "Test", "exercises": []}

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.create_training_plan(
                session,
                uuid4(),
                coach.coach_id,
                plan_data
            )

        assert "Coach has no club" in str(exc_info.value)


class TestGetTrainingPlanDetail:
    """Test get_training_plan_detail() function."""

    def test_get_training_plan_detail_success(
        self,
        session,
        sample_coach,
        sample_training_plan
    ):
        """Test successful training plan detail retrieval."""
        # Given: Training plan exists
        plan = sample_training_plan["plan"]

        # When: Get plan detail
        result = coach_service.get_training_plan_detail(
            session,
            plan.plan_id,
            sample_coach.coach_id
        )

        # Then: Returns correct structure
        assert "plan" in result
        assert "progress" in result
        assert "exercises" in result
        assert result["plan"]["plan_id"] == str(plan.plan_id)

    def test_get_training_plan_detail_with_progress(
        self,
        session,
        sample_coach,
        sample_training_plan
    ):
        """Test training plan detail includes progress."""
        # Given: Training plan with exercises
        plan = sample_training_plan["plan"]
        exercises = sample_training_plan["exercises"]

        # When: Get plan detail
        result = coach_service.get_training_plan_detail(
            session,
            plan.plan_id,
            sample_coach.coach_id
        )

        # Then: Progress is calculated
        assert "percentage" in result["progress"]
        assert "completed_exercises" in result["progress"]
        assert "total_exercises" in result["progress"]
        assert result["progress"]["total_exercises"] == len(exercises)

    def test_get_training_plan_detail_plan_not_found(self, session, sample_coach):
        """Test get_training_plan_detail with non-existent plan."""
        # Given: Random plan ID
        random_plan_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.get_training_plan_detail(
                session,
                random_plan_id,
                sample_coach.coach_id
            )

        assert "Training plan not found" in str(exc_info.value)


class TestUpdateTrainingPlan:
    """Test update_training_plan() function."""

    def test_update_training_plan_name_only(
        self,
        session,
        sample_coach,
        sample_training_plan
    ):
        """Test updating only plan name."""
        # Given: Training plan exists
        plan = sample_training_plan["plan"]
        update_data = {"plan_name": "Updated Name"}

        # When: Update plan
        result = coach_service.update_training_plan(
            session,
            plan.plan_id,
            sample_coach.coach_id,
            update_data
        )
        session.commit()

        # Then: Name is updated
        assert result["plan_name"] == "Updated Name"

        # Verify database state
        updated_plan = session.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan.plan_id
        ).first()
        assert updated_plan.plan_name == "Updated Name"

    def test_update_training_plan_update_existing_exercise(
        self,
        session,
        sample_coach,
        sample_training_plan
    ):
        """Test updating existing exercise."""
        # Given: Training plan with exercises
        plan = sample_training_plan["plan"]
        existing_exercise = sample_training_plan["exercises"][0]

        update_data = {
            "exercises": [
                {
                    "exercise_id": str(existing_exercise.exercise_id),
                    "exercise_name": "Updated Exercise",
                    "description": "Updated description",
                    "sets": "5",
                    "reps": "12",
                    "duration_minutes": "20",
                    "exercise_order": 1
                }
            ]
        }

        # When: Update plan
        coach_service.update_training_plan(
            session,
            plan.plan_id,
            sample_coach.coach_id,
            update_data
        )
        session.commit()

        # Then: Exercise is updated
        updated_exercise = session.query(TrainingExercise).filter(
            TrainingExercise.exercise_id == existing_exercise.exercise_id
        ).first()
        assert updated_exercise.exercise_name == "Updated Exercise"
        assert updated_exercise.sets == "5"

    def test_update_training_plan_add_new_exercise(
        self,
        session,
        sample_coach,
        sample_training_plan
    ):
        """Test adding new exercise to plan."""
        # Given: Training plan exists
        plan = sample_training_plan["plan"]
        original_count = len(sample_training_plan["exercises"])

        # Get existing exercise IDs
        existing_exercises = sample_training_plan["exercises"]
        exercises_data = [
            {
                "exercise_id": str(ex.exercise_id),
                "exercise_name": ex.exercise_name,
                "exercise_order": ex.exercise_order
            }
            for ex in existing_exercises
        ]

        # Add new exercise
        exercises_data.append({
            "exercise_name": "New Exercise",
            "description": "New description",
            "sets": "3",
            "reps": "10",
            "duration_minutes": "15",
            "exercise_order": original_count + 1
        })

        update_data = {"exercises": exercises_data}

        # When: Update plan
        coach_service.update_training_plan(
            session,
            plan.plan_id,
            sample_coach.coach_id,
            update_data
        )
        session.commit()

        # Then: New exercise is added
        all_exercises = session.query(TrainingExercise).filter(
            TrainingExercise.plan_id == plan.plan_id
        ).all()
        assert len(all_exercises) == original_count + 1

    def test_update_training_plan_delete_exercise(
        self,
        session,
        sample_coach,
        sample_training_plan
    ):
        """Test deleting exercise from plan."""
        # Given: Training plan with multiple exercises
        plan = sample_training_plan["plan"]
        keep_exercise = sample_training_plan["exercises"][0]

        update_data = {
            "exercises": [
                {
                    "exercise_id": str(keep_exercise.exercise_id),
                    "exercise_name": keep_exercise.exercise_name,
                    "exercise_order": 1
                }
            ]
        }

        # When: Update plan with only one exercise
        coach_service.update_training_plan(
            session,
            plan.plan_id,
            sample_coach.coach_id,
            update_data
        )
        session.commit()

        # Then: Other exercises are deleted
        remaining_exercises = session.query(TrainingExercise).filter(
            TrainingExercise.plan_id == plan.plan_id
        ).all()
        assert len(remaining_exercises) == 1

    def test_update_training_plan_flush_not_commit(
        self,
        session,
        sample_coach,
        sample_training_plan
    ):
        """Test that update_training_plan flushes but doesn't commit."""
        # Given: Training plan exists
        plan = sample_training_plan["plan"]
        update_data = {"plan_name": "Test Flush"}

        # When: Update plan
        coach_service.update_training_plan(
            session,
            plan.plan_id,
            sample_coach.coach_id,
            update_data
        )

        # Rollback to test flush behavior
        session.rollback()

        # Then: Changes are rolled back
        rolled_back_plan = session.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan.plan_id
        ).first()
        assert rolled_back_plan.plan_name != "Test Flush"

    def test_update_training_plan_plan_not_found(self, session, sample_coach):
        """Test update_training_plan with non-existent plan."""
        # Given: Random plan ID
        random_plan_id = uuid4()
        update_data = {"plan_name": "Test"}

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.update_training_plan(
                session,
                random_plan_id,
                sample_coach.coach_id,
                update_data
            )

        assert "Training plan not found" in str(exc_info.value)


class TestDeleteTrainingPlan:
    """Test delete_training_plan() function."""

    def test_delete_training_plan_success(
        self,
        session,
        sample_coach,
        sample_training_plan
    ):
        """Test successful training plan deletion."""
        # Given: Training plan exists
        plan = sample_training_plan["plan"]
        plan_id = plan.plan_id

        # When: Delete plan
        result = coach_service.delete_training_plan(
            session,
            plan_id,
            sample_coach.coach_id
        )
        session.commit()

        # Then: Plan is deleted
        assert result["deleted"] is True

        # Verify database state
        deleted_plan = session.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan_id
        ).first()
        assert deleted_plan is None

    def test_delete_training_plan_cascades_exercises(
        self,
        session,
        sample_coach,
        sample_training_plan
    ):
        """Test that deleting plan cascades to exercises."""
        # Given: Training plan with exercises
        plan = sample_training_plan["plan"]
        plan_id = plan.plan_id

        # When: Delete plan
        coach_service.delete_training_plan(
            session,
            plan_id,
            sample_coach.coach_id
        )
        session.commit()

        # Then: Exercises are also deleted
        exercises = session.query(TrainingExercise).filter(
            TrainingExercise.plan_id == plan_id
        ).all()
        assert len(exercises) == 0

    def test_delete_training_plan_flush_not_commit(
        self,
        session,
        sample_coach,
        sample_training_plan
    ):
        """Test that delete_training_plan flushes but doesn't commit."""
        # Given: Training plan exists
        plan = sample_training_plan["plan"]
        plan_id = plan.plan_id

        # When: Delete plan
        coach_service.delete_training_plan(
            session,
            plan_id,
            sample_coach.coach_id
        )

        # Rollback to test flush behavior
        session.rollback()

        # Then: Plan still exists after rollback
        plan_still_exists = session.query(TrainingPlan).filter(
            TrainingPlan.plan_id == plan_id
        ).first()
        assert plan_still_exists is not None

    def test_delete_training_plan_plan_not_found(self, session, sample_coach):
        """Test delete_training_plan with non-existent plan."""
        # Given: Random plan ID
        random_plan_id = uuid4()

        # When/Then: Raises ValueError
        with pytest.raises(ValueError) as exc_info:
            coach_service.delete_training_plan(
                session,
                random_plan_id,
                sample_coach.coach_id
            )

        assert "Training plan not found" in str(exc_info.value)
