"""
Tests for match statistics service.

Tests the calculation and storage of match statistics from StatsBomb events.
Follows TDD pattern with helper function tests and main function tests.
"""

import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date
from app.services.match_statistics_service import (
    calculate_match_statistics_from_events,
    insert_match_statistics
)
from app.models.match import Match
from app.models.club import Club
from app.models.opponent_club import OpponentClub
from app.models.match_statistics import MatchStatistics


# =============================================================================
# TEST FIXTURES - Event Creation Helpers
# =============================================================================

def create_pass_event(
    team_id: int = 217,
    location: list = None,
    pass_length: float = 10.0,
    pass_outcome_id: int = None,  # None = successful, 9 = incomplete
    pass_outcome_name: str = None,  # Outcome name (e.g., "Incomplete", "Out")
    is_cross: bool = False,
    pass_type_name: str = None,  # Pass type (e.g., "Throw-in", "Goal Kick", "Corner")
    period: int = 1,
    duration: float = 1.0,
    possession_id: int = 1
):
    """Create Pass event with configurable attributes."""
    if location is None:
        location = [50.0, 40.0]

    pass_data = {
        "length": pass_length,
        "end_location": [60.0, 45.0]
    }

    # Add pass type if specified (for set pieces)
    if pass_type_name is not None:
        pass_data["type"] = {"name": pass_type_name}

    # Handle outcome - prefer outcome_name over outcome_id
    if pass_outcome_name is not None:
        pass_data["outcome"] = {"name": pass_outcome_name}
    elif pass_outcome_id is not None:
        pass_data["outcome"] = {"id": pass_outcome_id, "name": "Incomplete"}

    if is_cross:
        pass_data["cross"] = True

    return {
        "id": str(uuid4()),
        "type": {"id": 30, "name": "Pass"},
        "team": {"id": team_id, "name": "Team"},
        "period": period,
        "location": location,
        "pass": pass_data,
        "possession": possession_id,
        "possession_team": {"id": team_id, "name": "Team"},
        "duration": duration
    }


def create_shot_event(
    team_id: int = 217,
    outcome_id: int = 100,  # 97=Goal, 100=Saved, 116=Saved to Post, 98=Off T, 99=Post, 101=Wayward
    statsbomb_xg: float = 0.25,
    period: int = 1,
    duration: float = 1.0,
    possession_id: int = 1
):
    """Create Shot event with configurable outcome and xG."""
    return {
        "id": str(uuid4()),
        "type": {"id": 16, "name": "Shot"},
        "team": {"id": team_id, "name": "Team"},
        "period": period,
        "shot": {
            "outcome": {"id": outcome_id, "name": "Saved"},
            "statsbomb_xg": statsbomb_xg
        },
        "possession": possession_id,
        "possession_team": {"id": team_id, "name": "Team"},
        "duration": duration
    }


def create_dribble_event(
    team_id: int = 217,
    outcome_name: str = "Complete",  # "Complete" or "Incomplete"
    period: int = 1,
    duration: float = 1.0,
    possession_id: int = 1
):
    """Create Dribble event (Complete/Incomplete)."""
    return {
        "id": str(uuid4()),
        "type": {"id": 14, "name": "Dribble"},
        "team": {"id": team_id, "name": "Team"},
        "period": period,
        "dribble": {
            "outcome": {"name": outcome_name}
        },
        "possession": possession_id,
        "possession_team": {"id": team_id, "name": "Team"},
        "duration": duration
    }


def create_duel_event(
    team_id: int = 217,
    duel_type_name: str = "Tackle",  # "Tackle", "Aerial Lost", etc.
    outcome_id: int = 4,  # 4=Won, 15=Success, 16=Success In Play, 17=Success Out
    period: int = 1,
    duration: float = 1.0,
    possession_id: int = 1
):
    """Create Duel event with configurable type and outcome."""
    return {
        "id": str(uuid4()),
        "type": {"id": 4, "name": "Duel"},
        "team": {"id": team_id, "name": "Team"},
        "period": period,
        "duel": {
            "type": {"name": duel_type_name},
            "outcome": {"id": outcome_id, "name": "Won"}
        },
        "possession": possession_id,
        "possession_team": {"id": team_id, "name": "Team"},
        "duration": duration
    }


def create_interception_event(
    team_id: int = 217,
    period: int = 1,
    duration: float = 1.0,
    possession_id: int = 1
):
    """Create Interception event."""
    return {
        "id": str(uuid4()),
        "type": {"id": 10, "name": "Interception"},
        "team": {"id": team_id, "name": "Team"},
        "period": period,
        "possession": possession_id,
        "possession_team": {"id": team_id, "name": "Team"},
        "duration": duration
    }


def create_ball_recovery_event(
    team_id: int = 217,
    recovery_failure: bool = False,
    period: int = 1,
    duration: float = 1.0,
    possession_id: int = 1
):
    """Create Ball Recovery event with optional failure flag."""
    event = {
        "id": str(uuid4()),
        "type": {"id": 2, "name": "Ball Recovery"},
        "team": {"id": team_id, "name": "Team"},
        "period": period,
        "possession": possession_id,
        "possession_team": {"id": team_id, "name": "Team"},
        "duration": duration
    }

    if recovery_failure:
        event["ball_recovery"] = {"recovery_failure": True}

    return event


def create_possession_event(
    possession_id: int,
    team_id: int,
    duration: float = 1.0,
    period: int = 1
):
    """Create event with specific possession sequence ID, team, and duration.

    Uses Carry event type (43) which doesn't affect pass/shot/dribble/tackle statistics.
    """
    return {
        "id": str(uuid4()),
        "type": {"id": 43, "name": "Carry"},
        "team": {"id": team_id, "name": "Team"},
        "period": period,
        "possession": possession_id,
        "possession_team": {"id": team_id, "name": "Team"},
        "duration": duration
    }


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

class TestCalculateMatchStatisticsFromEvents:
    """Test calculate_match_statistics_from_events helper function."""

    def test_calculates_possession_percentage_correctly(self):
        """Test possession calculated by summing event durations."""
        # Given: Events with varying durations
        events = [
            create_possession_event(possession_id=1, team_id=217, duration=10.0),  # Our team
            create_possession_event(possession_id=2, team_id=206, duration=5.0),   # Opponent
            create_possession_event(possession_id=3, team_id=217, duration=15.0),  # Our team
            create_possession_event(possession_id=4, team_id=206, duration=10.0),  # Opponent
            create_possession_event(possession_id=5, team_id=217, duration=5.0),   # Our team
        ]
        # Our team total: 10 + 15 + 5 = 30 seconds
        # Opponent total: 5 + 10 = 15 seconds
        # Total: 45 seconds
        # Our team: 30/45 = 66.67%
        # Opponent: 15/45 = 33.33%

        # When: Calculate statistics
        result = calculate_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Possession percentage should be based on duration
        assert result['our_team']['possession_percentage'] == Decimal('66.67')
        assert result['opponent_team']['possession_percentage'] == Decimal('33.33')

    def test_calculates_expected_goals_sum(self):
        """Test xG is sum of all shot.statsbomb_xg values."""
        # Given: Multiple shots with xG values
        events = [
            create_shot_event(team_id=217, statsbomb_xg=0.35),
            create_shot_event(team_id=217, statsbomb_xg=0.12),
            create_shot_event(team_id=206, statsbomb_xg=0.78),
            create_shot_event(team_id=217, statsbomb_xg=0.03),
            create_shot_event(team_id=206, statsbomb_xg=0.45)
        ]

        # When: Calculate statistics
        result = calculate_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Sum xG for each team
        assert result['our_team']['expected_goals'] == Decimal('0.500000')  # 0.35+0.12+0.03
        assert result['opponent_team']['expected_goals'] == Decimal('1.230000')  # 0.78+0.45

    def test_categorizes_shots_by_outcome(self):
        """Test shots categorized into on target (97,100,116) vs off target (98,99,101)."""
        # Given: Mix of shot outcomes
        events = [
            create_shot_event(team_id=217, outcome_id=97),   # Goal - ON TARGET
            create_shot_event(team_id=217, outcome_id=100),  # Saved - ON TARGET
            create_shot_event(team_id=217, outcome_id=116),  # Saved to Post - ON TARGET
            create_shot_event(team_id=217, outcome_id=98),   # Off T - OFF TARGET
            create_shot_event(team_id=217, outcome_id=99),   # Post - OFF TARGET
            create_shot_event(team_id=217, outcome_id=101),  # Wayward - OFF TARGET
            create_shot_event(team_id=206, outcome_id=97),   # Opponent goal
            create_shot_event(team_id=206, outcome_id=99),   # Opponent off target
        ]

        # When: Calculate statistics
        result = calculate_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Verify shot categorization
        assert result['our_team']['total_shots'] == 6
        assert result['our_team']['shots_on_target'] == 3  # 97, 100, 116
        assert result['our_team']['shots_off_target'] == 3  # 98, 99, 101
        assert result['opponent_team']['total_shots'] == 2
        assert result['opponent_team']['shots_on_target'] == 1  # 97
        assert result['opponent_team']['shots_off_target'] == 1  # 99

    def test_counts_goalkeeper_saves_from_opponent_shots(self):
        """Test GK saves counted from OPPONENT'S shots with outcome 100 or 116."""
        # Given: Shots from both teams with saved outcomes
        events = [
            create_shot_event(team_id=217, outcome_id=100),  # Our shot saved (opponent GK)
            create_shot_event(team_id=217, outcome_id=116),  # Our shot saved to post (opponent GK)
            create_shot_event(team_id=206, outcome_id=100),  # Opponent shot saved (our GK)
            create_shot_event(team_id=206, outcome_id=116),  # Opponent shot saved to post (our GK)
            create_shot_event(team_id=206, outcome_id=97),   # Opponent goal (not a save)
            create_shot_event(team_id=217, outcome_id=97),   # Our goal (not a save)
        ]

        # When: Calculate statistics
        result = calculate_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Our GK saves = opponent's saved shots (100, 116)
        assert result['our_team']['goalkeeper_saves'] == 2   # 206's shots with outcome 100, 116
        assert result['opponent_team']['goalkeeper_saves'] == 2  # 217's shots with outcome 100, 116

    def test_counts_total_and_completed_passes(self):
        """Test pass counting and completion rate calculation."""
        # Given: Mix of completed and incomplete passes
        events = [
            create_pass_event(team_id=217),  # Completed (no outcome = success)
            create_pass_event(team_id=217),  # Completed
            create_pass_event(team_id=217, pass_outcome_name="Incomplete"),  # Incomplete
            create_pass_event(team_id=206),  # Opponent completed
            create_pass_event(team_id=217),  # Completed
            create_pass_event(team_id=217, pass_outcome_name="Incomplete"),  # Incomplete
        ]

        # When: Calculate statistics
        result = calculate_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Verify pass stats
        assert result['our_team']['total_passes'] == 5
        assert result['our_team']['passes_completed'] == 3
        assert result['our_team']['pass_completion_rate'] == Decimal('60.00')  # 3/5 * 100
        assert result['opponent_team']['total_passes'] == 1
        assert result['opponent_team']['passes_completed'] == 1
        assert result['opponent_team']['pass_completion_rate'] == Decimal('100.00')

    def test_counts_passes_in_final_third(self):
        """Test passes in final third counted when location[0] >= 80."""
        # Given: Passes at different field locations
        events = [
            create_pass_event(team_id=217, location=[85.0, 40.0]),  # Final third
            create_pass_event(team_id=217, location=[90.5, 20.0]),  # Final third
            create_pass_event(team_id=217, location=[75.0, 40.0]),  # NOT final third
            create_pass_event(team_id=217, location=[80.0, 40.0]),  # Final third (>=80)
            create_pass_event(team_id=206, location=[95.0, 40.0]),  # Opponent final third
        ]

        # When: Calculate statistics
        result = calculate_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Count passes with location[0] >= 80
        assert result['our_team']['passes_in_final_third'] == 3
        assert result['opponent_team']['passes_in_final_third'] == 1

    def test_counts_long_passes_and_crosses(self):
        """Test long passes (length > 30) and crosses counted separately."""
        # Given: Mix of pass types
        events = [
            create_pass_event(team_id=217, pass_length=35.0),  # Long pass
            create_pass_event(team_id=217, pass_length=15.0),  # Short pass
            create_pass_event(team_id=217, pass_length=40.0, is_cross=True),  # Long cross
            create_pass_event(team_id=217, is_cross=True),  # Short cross
            create_pass_event(team_id=206, pass_length=50.0),  # Opponent long pass
        ]

        # When: Calculate statistics
        result = calculate_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Verify long passes and crosses
        assert result['our_team']['long_passes'] == 2  # length > 30
        assert result['our_team']['crosses'] == 2  # cross = True
        assert result['opponent_team']['long_passes'] == 1

    def test_counts_dribbles_with_success_rate(self):
        """Test dribble counting based on outcome (Complete/Incomplete)."""
        # Given: Mix of successful and unsuccessful dribbles
        events = [
            create_dribble_event(team_id=217, outcome_name="Complete"),
            create_dribble_event(team_id=217, outcome_name="Complete"),
            create_dribble_event(team_id=217, outcome_name="Incomplete"),
            create_dribble_event(team_id=206, outcome_name="Complete"),
            create_dribble_event(team_id=217, outcome_name="Incomplete"),
        ]

        # When: Calculate statistics
        result = calculate_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Count dribbles
        assert result['our_team']['total_dribbles'] == 4
        assert result['our_team']['successful_dribbles'] == 2
        assert result['opponent_team']['total_dribbles'] == 1
        assert result['opponent_team']['successful_dribbles'] == 1

    def test_counts_tackles_with_success_percentage(self):
        """Test tackle counting from Duel events with 'Tackle' in type name."""
        # Given: Mix of duels including tackles
        events = [
            create_duel_event(team_id=217, duel_type_name="Tackle", outcome_id=4),    # Won
            create_duel_event(team_id=217, duel_type_name="Tackle", outcome_id=15),   # Success
            create_duel_event(team_id=217, duel_type_name="Tackle", outcome_id=5),    # Lost (not in success IDs)
            create_duel_event(team_id=217, duel_type_name="Aerial Lost", outcome_id=5),  # NOT tackle
            create_duel_event(team_id=217, duel_type_name="Tackle", outcome_id=16),   # Success In Play
            create_duel_event(team_id=206, duel_type_name="Tackle", outcome_id=17),   # Success Out
        ]

        # When: Calculate statistics
        result = calculate_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Count tackles and calculate success %
        assert result['our_team']['total_tackles'] == 4  # Excludes Aerial Lost
        # Success: 3 (IDs 4, 15, 16) out of 4 total = 75.00%
        assert result['our_team']['tackle_success_percentage'] == Decimal('75.00')
        assert result['opponent_team']['total_tackles'] == 1
        assert result['opponent_team']['tackle_success_percentage'] == Decimal('100.00')

    def test_counts_interceptions_and_ball_recoveries(self):
        """Test counting of Interception and Ball Recovery events (excluding failed recoveries)."""
        # Given: Mix of defensive actions
        events = [
            create_interception_event(team_id=217),
            create_interception_event(team_id=217),
            create_ball_recovery_event(team_id=217),  # Successful recovery
            create_ball_recovery_event(team_id=217, recovery_failure=True),  # Failed - DON'T count
            create_interception_event(team_id=206),
            create_ball_recovery_event(team_id=217),  # Successful recovery
            create_ball_recovery_event(team_id=206),  # Opponent successful
            create_ball_recovery_event(team_id=206, recovery_failure=True),  # Failed - DON'T count
        ]

        # When: Calculate statistics
        result = calculate_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Count each type (exclude failed recoveries)
        assert result['our_team']['interceptions'] == 2
        assert result['our_team']['ball_recoveries'] == 2  # Exclude failure
        assert result['opponent_team']['interceptions'] == 1
        assert result['opponent_team']['ball_recoveries'] == 1  # Exclude failure

    def test_handles_empty_events_list(self):
        """Test returns all statistics as None/0 for empty events."""
        # Given: Empty events list
        events = []

        # When: Calculate statistics
        result = calculate_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: All numeric stats should be 0, percentages should be None
        assert result['our_team']['possession_percentage'] is None
        assert result['our_team']['expected_goals'] == Decimal('0')
        assert result['our_team']['total_shots'] == 0
        assert result['our_team']['total_passes'] == 0
        assert result['our_team']['pass_completion_rate'] is None
        assert result['our_team']['tackle_success_percentage'] is None

    def test_handles_division_by_zero_for_percentages(self):
        """Test percentage fields are None when denominator is 0."""
        # Given: Events with no passes or tackles
        events = [
            create_shot_event(team_id=217),  # Shot but no passes
            create_dribble_event(team_id=217),  # Dribble but no tackles
        ]

        # When: Calculate statistics
        result = calculate_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Percentage fields should be None when can't calculate
        assert result['our_team']['pass_completion_rate'] is None  # No passes
        assert result['our_team']['tackle_success_percentage'] is None  # No tackles
        # Opponent has no events, so possession should also be None
        assert result['opponent_team']['possession_percentage'] is None  # No possessions

    def test_returns_correct_dict_structure(self):
        """Test return value has 'our_team' and 'opponent_team' keys with all fields."""
        # Given: Sample events
        events = [
            create_pass_event(team_id=217),
            create_shot_event(team_id=206)
        ]

        # When: Calculate statistics
        result = calculate_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Verify structure
        assert 'our_team' in result
        assert 'opponent_team' in result

        # Verify all required fields exist
        required_fields = [
            'possession_percentage', 'expected_goals', 'total_shots',
            'shots_on_target', 'shots_off_target', 'goalkeeper_saves',
            'total_passes', 'passes_completed', 'pass_completion_rate',
            'passes_in_final_third', 'long_passes', 'crosses',
            'total_dribbles', 'successful_dribbles', 'total_tackles',
            'tackle_success_percentage', 'interceptions', 'ball_recoveries'
        ]

        for field in required_fields:
            assert field in result['our_team']
            assert field in result['opponent_team']

    def test_excludes_penalty_shootout_events(self):
        """Test events from period 5 (penalty shootout) are excluded."""
        # Given: Mix of regular and penalty shootout events
        events = [
            create_shot_event(team_id=217, period=1),  # Regular - COUNT
            create_pass_event(team_id=217, period=5),  # Penalty shootout - EXCLUDE
            create_shot_event(team_id=217, period=2),  # Regular - COUNT
            create_pass_event(team_id=217, period=5),  # Penalty shootout - EXCLUDE
        ]

        # When: Calculate statistics
        result = calculate_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Should only count 2 shots, 0 passes (period 5 excluded)
        assert result['our_team']['total_shots'] == 2
        assert result['our_team']['total_passes'] == 0

    def test_handles_missing_optional_fields(self):
        """Test gracefully handles events missing optional fields."""
        # Given: Events with missing optional fields
        events = [
            {
                "id": str(uuid4()),
                "type": {"id": 30, "name": "Pass"},
                "team": {"id": 217, "name": "Team"},
                "period": 1,
                "possession": 1,
                "possession_team": {"id": 217, "name": "Team"},
                "duration": 1.0,
                # Missing: pass.length, pass.cross, location, etc.
                "pass": {}
            },
            {
                "id": str(uuid4()),
                "type": {"id": 16, "name": "Shot"},
                "team": {"id": 217, "name": "Team"},
                "period": 1,
                "possession": 1,
                "possession_team": {"id": 217, "name": "Team"},
                "duration": 1.0,
                "shot": {
                    # Missing: statsbomb_xg
                    "outcome": {"id": 100, "name": "Saved"}
                }
            }
        ]

        # When: Calculate statistics
        result = calculate_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Should not crash, count events that can be processed
        assert result['our_team']['total_passes'] == 1  # Pass counted
        assert result['our_team']['long_passes'] == 0  # No length available
        assert result['our_team']['crosses'] == 0  # No cross field
        assert result['our_team']['total_shots'] == 1
        assert result['our_team']['expected_goals'] == Decimal('0')  # Missing xG = 0


# =============================================================================
# MAIN FUNCTION TESTS
# =============================================================================

class TestInsertMatchStatistics:
    """Test insert_match_statistics main database function."""

    @pytest.fixture
    def match_with_clubs(self, session):
        """Create match with club and opponent for testing."""
        club = Club(coach_id=uuid4(), club_name="Test Club")
        opponent = OpponentClub(opponent_name="Opponent Club")
        session.add(club)
        session.add(opponent)
        session.commit()

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent.opponent_club_id,
            opponent_name="Opponent Club",
            match_date=date(2022, 12, 18),
            our_score=0,
            opponent_score=0,
            result='D'
        )
        session.add(match)
        session.commit()
        return match

    def test_inserts_two_statistics_records_into_database(self, session, match_with_clubs):
        """Test that insert_match_statistics creates 2 MatchStatistics records."""
        # Given: Match exists in database
        match = match_with_clubs

        # And: Events with statistics
        events = [
            create_shot_event(team_id=217, outcome_id=97, statsbomb_xg=0.5),
            create_shot_event(team_id=206, outcome_id=100, statsbomb_xg=0.3),
            create_pass_event(team_id=217, location=[85.0, 40.0]),
            create_pass_event(team_id=206, pass_outcome_id=9)
        ]

        # When: Insert statistics
        result = insert_match_statistics(
            db=session,
            match_id=match.match_id,
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Returns 2 (number of records inserted)
        assert result == 2

        # And: 2 MatchStatistics records exist in database
        stats_records = session.query(MatchStatistics).filter(
            MatchStatistics.match_id == match.match_id
        ).all()
        assert len(stats_records) == 2

    def test_raises_error_if_match_not_found(self, session):
        """Test that insert_match_statistics raises ValueError if match doesn't exist."""
        # Given: Non-existent match ID
        fake_match_id = uuid4()
        events = [create_shot_event()]

        # When/Then: Raises ValueError
        with pytest.raises(ValueError, match=f"Match with ID {fake_match_id} not found"):
            insert_match_statistics(
                db=session,
                match_id=fake_match_id,
                events=events,
                our_club_statsbomb_id=217,
                opponent_statsbomb_id=206
            )

    def test_raises_error_if_statistics_already_exist(self, session, match_with_clubs):
        """Test that insert_match_statistics raises ValueError if statistics already exist."""
        # Given: Match with existing statistics
        match = match_with_clubs
        existing_stats = MatchStatistics(
            match_id=match.match_id,
            team_type='our_team',
            possession_percentage=Decimal('50.00'),
            expected_goals=Decimal('1.5'),
            total_shots=10
        )
        session.add(existing_stats)
        session.commit()

        # When/Then: Raises ValueError
        events = [create_shot_event()]
        with pytest.raises(ValueError, match="Statistics already exist for match"):
            insert_match_statistics(
                db=session,
                match_id=match.match_id,
                events=events,
                our_club_statsbomb_id=217,
                opponent_statsbomb_id=206
            )

    def test_handles_empty_events_list(self, session, match_with_clubs):
        """Test that insert_match_statistics handles empty events list correctly."""
        # Given: Match exists
        match = match_with_clubs

        # When: Insert with empty events
        result = insert_match_statistics(
            db=session,
            match_id=match.match_id,
            events=[],
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Returns 2
        assert result == 2

        # And: Statistics exist with 0/None values
        stats = session.query(MatchStatistics).filter(
            MatchStatistics.match_id == match.match_id
        ).all()
        assert len(stats) == 2

        for stat in stats:
            assert stat.possession_percentage is None
            assert stat.expected_goals == Decimal('0')
            assert stat.total_shots == 0
            assert stat.total_passes == 0

    def test_stores_all_statistics_fields_correctly(self, session, match_with_clubs):
        """Test that all 18 statistics fields are stored correctly."""
        # Given: Match exists
        match = match_with_clubs

        # And: Events with all statistic types
        events = [
            # Possession events
            create_possession_event(possession_id=1, team_id=217, duration=30.0),
            create_possession_event(possession_id=2, team_id=206, duration=20.0),
            # Shots
            create_shot_event(team_id=217, outcome_id=97, statsbomb_xg=0.8),  # Goal (on target)
            create_shot_event(team_id=217, outcome_id=100, statsbomb_xg=0.4),  # Saved (on target)
            create_shot_event(team_id=217, outcome_id=98, statsbomb_xg=0.1),  # Off target
            create_shot_event(team_id=206, outcome_id=116, statsbomb_xg=0.5),  # Saved to Post (on target)
            # Passes
            create_pass_event(team_id=217, location=[85.0, 40.0]),  # Final third
            create_pass_event(team_id=217, pass_length=35.0),  # Long pass
            create_pass_event(team_id=217, is_cross=True),  # Cross
            create_pass_event(team_id=217, pass_outcome_id=9),  # Incomplete
            # Dribbles
            create_dribble_event(team_id=217, outcome_name="Complete"),
            create_dribble_event(team_id=217, outcome_name="Incomplete"),
            # Tackles
            create_duel_event(team_id=217, duel_type_name="Tackle", outcome_id=4),  # Won
            create_duel_event(team_id=217, duel_type_name="Tackle", outcome_id=1),  # Lost
            # Interceptions and Ball Recoveries
            create_interception_event(team_id=217),
            create_ball_recovery_event(team_id=217, recovery_failure=False),
            create_ball_recovery_event(team_id=217, recovery_failure=True)  # Should not count
        ]

        # When: Insert statistics
        insert_match_statistics(
            db=session,
            match_id=match.match_id,
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: All fields stored correctly for our_team
        our_stats = session.query(MatchStatistics).filter(
            MatchStatistics.match_id == match.match_id,
            MatchStatistics.team_type == 'our_team'
        ).first()

        # Possession: All events contribute (217: 30+3+4+2+2+1+2=44, 206: 20+1=21, total=65, 44/65=67.69%)
        assert our_stats.possession_percentage == Decimal('67.69')
        assert our_stats.expected_goals == Decimal('1.30')  # 0.8 + 0.4 + 0.1
        assert our_stats.total_shots == 3
        assert our_stats.shots_on_target == 2  # 97, 100
        assert our_stats.shots_off_target == 1  # 98
        assert our_stats.goalkeeper_saves == 1  # Opponent shot 116
        assert our_stats.total_passes == 4
        assert our_stats.passes_completed == 3
        assert our_stats.pass_completion_rate == Decimal('75.00')
        assert our_stats.passes_in_final_third == 1
        assert our_stats.long_passes == 1
        assert our_stats.crosses == 1
        assert our_stats.total_dribbles == 2
        assert our_stats.successful_dribbles == 1
        assert our_stats.total_tackles == 2
        assert our_stats.tackle_success_percentage == Decimal('50.00')
        assert our_stats.interceptions == 1
        assert our_stats.ball_recoveries == 1  # Excludes recovery_failure=True

    def test_commits_transaction_successfully(self, session, match_with_clubs):
        """Test that insert_match_statistics commits data to database."""
        # Given: Match exists
        match = match_with_clubs

        # When: Insert statistics
        events = [create_shot_event(team_id=217)]
        insert_match_statistics(
            db=session,
            match_id=match.match_id,
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Data persists after closing session (query in new transaction)
        session.expire_all()  # Force fresh query
        stats = session.query(MatchStatistics).filter(
            MatchStatistics.match_id == match.match_id
        ).all()
        assert len(stats) == 2

    def test_sets_team_type_correctly(self, session, match_with_clubs):
        """Test that team_type is set to 'our_team' and 'opponent_team'."""
        # Given: Match exists
        match = match_with_clubs

        # When: Insert statistics
        events = [create_shot_event(team_id=217)]
        insert_match_statistics(
            db=session,
            match_id=match.match_id,
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: One record has team_type='our_team', other has 'opponent_team'
        stats = session.query(MatchStatistics).filter(
            MatchStatistics.match_id == match.match_id
        ).all()

        team_types = {s.team_type for s in stats}
        assert team_types == {'our_team', 'opponent_team'}

    def test_excludes_penalty_shootout_events(self, session, match_with_clubs):
        """Test that period 5 (penalty shootout) events are excluded from statistics."""
        # Given: Match exists
        match = match_with_clubs

        # And: Events include period 5 (penalty shootout)
        events = [
            # Regular time shots
            create_shot_event(team_id=217, outcome_id=97, period=1, statsbomb_xg=0.5),
            create_shot_event(team_id=217, outcome_id=100, period=2, statsbomb_xg=0.3),
            # Penalty shootout (should be excluded)
            create_shot_event(team_id=217, outcome_id=97, period=5, statsbomb_xg=0.9),
            create_shot_event(team_id=217, outcome_id=97, period=5, statsbomb_xg=0.9)
        ]

        # When: Insert statistics
        insert_match_statistics(
            db=session,
            match_id=match.match_id,
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Only regular time events counted
        our_stats = session.query(MatchStatistics).filter(
            MatchStatistics.match_id == match.match_id,
            MatchStatistics.team_type == 'our_team'
        ).first()

        assert our_stats.total_shots == 2  # Not 4
        assert our_stats.expected_goals == Decimal('0.80')  # 0.5 + 0.3, not 2.6
