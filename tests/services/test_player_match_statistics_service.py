"""
Tests for player match statistics service.

Tests the calculation and storage of individual player statistics from StatsBomb events.
Follows TDD pattern with helper function tests and main function tests.
"""

import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date
from app.services.player_match_statistics_service import (
    calculate_player_match_statistics_from_events,
    insert_player_match_statistics
)
from app.models.match import Match
from app.models.club import Club
from app.models.opponent_club import OpponentClub
from app.models.player import Player
from app.models.match_lineup import MatchLineup
from app.models.player_match_statistics import PlayerMatchStatistics


# =============================================================================
# TEST FIXTURES - Event Creation Helpers
# =============================================================================

def create_shot_event(
    team_id: int = 217,
    player_id: int = 5503,  # StatsBomb player ID
    outcome_id: int = 100,  # 97=Goal, 100=Saved, 116=Saved to Post, 98=Off T, 99=Post, 101=Wayward
    statsbomb_xg: float = 0.25,
    period: int = 1,
    duration: float = 1.0,
    possession_id: int = 1
):
    """Create Shot event with player attribution."""
    return {
        "id": str(uuid4()),
        "type": {"id": 16, "name": "Shot"},
        "team": {"id": team_id, "name": "Team"},
        "player": {"id": player_id, "name": "Player"},
        "period": period,
        "shot": {
            "outcome": {"id": outcome_id, "name": "Saved"},
            "statsbomb_xg": statsbomb_xg
        },
        "possession": possession_id,
        "possession_team": {"id": team_id, "name": "Team"},
        "duration": duration
    }


def create_pass_event(
    team_id: int = 217,
    player_id: int = 5503,
    location: list = None,
    pass_length: float = 10.0,
    pass_outcome_name: str = None,  # None = completed, "Incomplete", "Out", etc.
    is_cross: bool = False,
    pass_type_name: str = None,  # "Throw-in", "Goal Kick", "Corner"
    goal_assist: bool = False,  # For assists
    period: int = 1,
    duration: float = 1.0,
    possession_id: int = 1
):
    """Create Pass event with player attribution."""
    if location is None:
        location = [50.0, 40.0]

    pass_data = {
        "length": pass_length,
        "end_location": [60.0, 45.0]
    }

    # Add pass type if specified (for set pieces)
    if pass_type_name is not None:
        pass_data["type"] = {"name": pass_type_name}

    # Handle outcome
    if pass_outcome_name is not None:
        pass_data["outcome"] = {"name": pass_outcome_name}

    # Add goal assist flag
    if goal_assist:
        pass_data["goal_assist"] = True

    # Add cross flag
    if is_cross:
        pass_data["cross"] = True

    return {
        "id": str(uuid4()),
        "type": {"id": 30, "name": "Pass"},
        "team": {"id": team_id, "name": "Team"},
        "player": {"id": player_id, "name": "Player"},
        "period": period,
        "location": location,
        "pass": pass_data,
        "possession": possession_id,
        "possession_team": {"id": team_id, "name": "Team"},
        "duration": duration
    }


def create_dribble_event(
    team_id: int = 217,
    player_id: int = 5503,
    outcome_name: str = "Complete",  # "Complete" or "Incomplete"
    period: int = 1,
    duration: float = 1.0,
    possession_id: int = 1
):
    """Create Dribble event with player attribution."""
    return {
        "id": str(uuid4()),
        "type": {"id": 14, "name": "Dribble"},
        "team": {"id": team_id, "name": "Team"},
        "player": {"id": player_id, "name": "Player"},
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
    player_id: int = 5503,
    duel_type_name: str = "Tackle",  # "Tackle", "Aerial Lost", etc.
    outcome_id: int = 4,  # 4=Won, 15=Success, 16=Success In Play, 17=Success Out
    period: int = 1,
    duration: float = 1.0,
    possession_id: int = 1
):
    """Create Duel event with player attribution."""
    return {
        "id": str(uuid4()),
        "type": {"id": 4, "name": "Duel"},
        "team": {"id": team_id, "name": "Team"},
        "player": {"id": player_id, "name": "Player"},
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
    player_id: int = 5503,
    outcome_id: int = None,  # 4=Won, 15=Success, 16=Success In Play, 17=Success Out
    period: int = 1,
    duration: float = 1.0,
    possession_id: int = 1
):
    """Create Interception event with optional outcome for success tracking."""
    event = {
        "id": str(uuid4()),
        "type": {"id": 10, "name": "Interception"},
        "team": {"id": team_id, "name": "Team"},
        "player": {"id": player_id, "name": "Player"},
        "period": period,
        "possession": possession_id,
        "possession_team": {"id": team_id, "name": "Team"},
        "duration": duration
    }

    # Add outcome if specified (for success tracking)
    if outcome_id is not None:
        event["interception"] = {
            "outcome": {"id": outcome_id, "name": "Won"}
        }

    return event


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

class TestCalculatePlayerMatchStatisticsFromEvents:
    """Test calculate_player_match_statistics_from_events() pure processing function."""

    def test_calculates_goals_from_shot_events(self):
        """Test that goals are correctly counted from Shot events with outcome 97 (Goal)."""
        events = [
            create_shot_event(player_id=5503, outcome_id=97),  # Goal
            create_shot_event(player_id=5503, outcome_id=100),  # Saved (not a goal)
            create_shot_event(player_id=5503, outcome_id=97),  # Goal
            create_shot_event(player_id=6543, outcome_id=97),  # Different player goal
        ]

        result = calculate_player_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        assert result[5503]['goals'] == 2
        assert result[6543]['goals'] == 1

    def test_calculates_assists_from_pass_events(self):
        """Test that assists are correctly counted from Pass events with goal_assist flag."""
        events = [
            create_pass_event(player_id=5503, goal_assist=True),  # Assist
            create_pass_event(player_id=5503, goal_assist=False),  # Regular pass
            create_pass_event(player_id=5503, goal_assist=True),  # Assist
            create_pass_event(player_id=6543, goal_assist=True),  # Different player assist
        ]

        result = calculate_player_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        assert result[5503]['assists'] == 2
        assert result[6543]['assists'] == 1

    def test_calculates_expected_goals_sum(self):
        """Test that xG is summed correctly from shot.statsbomb_xg values."""
        events = [
            create_shot_event(player_id=5503, statsbomb_xg=0.25, outcome_id=100),
            create_shot_event(player_id=5503, statsbomb_xg=0.80, outcome_id=97),
            create_shot_event(player_id=5503, statsbomb_xg=0.15, outcome_id=98),
            create_shot_event(player_id=6543, statsbomb_xg=0.40, outcome_id=100),
        ]

        result = calculate_player_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        # Player 5503: 0.25 + 0.80 + 0.15 = 1.20
        assert result[5503]['expected_goals'] == Decimal('1.20')
        assert result[6543]['expected_goals'] == Decimal('0.40')

    def test_categorizes_shots_by_outcome(self):
        """Test shots are counted and categorized correctly by outcome."""
        events = [
            create_shot_event(player_id=5503, outcome_id=97),   # Goal (on target)
            create_shot_event(player_id=5503, outcome_id=100),  # Saved (on target)
            create_shot_event(player_id=5503, outcome_id=116),  # Saved to Post (on target)
            create_shot_event(player_id=5503, outcome_id=98),   # Off Target
            create_shot_event(player_id=5503, outcome_id=99),   # Post
            create_shot_event(player_id=5503, outcome_id=101),  # Wayward
        ]

        result = calculate_player_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        assert result[5503]['shots'] == 6
        assert result[5503]['shots_on_target'] == 3  # 97, 100, 116

    def test_counts_total_and_completed_passes(self):
        """Test pass counting with completion logic (excluding set pieces)."""
        events = [
            # Regular passes
            create_pass_event(player_id=5503, pass_outcome_name=None),  # Completed
            create_pass_event(player_id=5503, pass_outcome_name="Incomplete"),  # Failed
            create_pass_event(player_id=5503, pass_outcome_name=None),  # Completed
            # Set pieces (should be excluded from total_passes)
            create_pass_event(player_id=5503, pass_type_name="Throw-in"),
            create_pass_event(player_id=5503, pass_type_name="Goal Kick"),
            create_pass_event(player_id=5503, pass_type_name="Corner"),
        ]

        result = calculate_player_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        assert result[5503]['total_passes'] == 3  # Excludes set pieces
        assert result[5503]['completed_passes'] == 2  # Only passes with outcome=None

    def test_counts_short_and_long_passes(self):
        """Test pass categorization by length (short <= 30, long > 30)."""
        events = [
            create_pass_event(player_id=5503, pass_length=10.0),  # Short
            create_pass_event(player_id=5503, pass_length=30.0),  # Short (boundary)
            create_pass_event(player_id=5503, pass_length=30.1),  # Long
            create_pass_event(player_id=5503, pass_length=50.0),  # Long
            # Set piece (should be excluded)
            create_pass_event(player_id=5503, pass_length=20.0, pass_type_name="Throw-in"),
        ]

        result = calculate_player_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        assert result[5503]['short_passes'] == 2  # <= 30
        assert result[5503]['long_passes'] == 2   # > 30

    def test_counts_final_third_passes_and_crosses(self):
        """Test final third passes (location[0] >= 80) and crosses."""
        events = [
            create_pass_event(player_id=5503, location=[80.0, 40.0]),  # Final third (boundary)
            create_pass_event(player_id=5503, location=[90.0, 40.0]),  # Final third
            create_pass_event(player_id=5503, location=[79.9, 40.0]),  # Not final third
            create_pass_event(player_id=5503, location=[85.0, 40.0], is_cross=True),  # Final third + cross
            create_pass_event(player_id=5503, location=[50.0, 40.0], is_cross=True),  # Cross (not final third)
        ]

        result = calculate_player_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        assert result[5503]['final_third_passes'] == 3  # >= 80
        assert result[5503]['crosses'] == 2

    def test_counts_dribbles_with_success_rate(self):
        """Test dribble counting with success tracking."""
        events = [
            create_dribble_event(player_id=5503, outcome_name="Complete"),
            create_dribble_event(player_id=5503, outcome_name="Incomplete"),
            create_dribble_event(player_id=5503, outcome_name="Complete"),
            create_dribble_event(player_id=5503, outcome_name="Complete"),
        ]

        result = calculate_player_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        assert result[5503]['total_dribbles'] == 4
        assert result[5503]['successful_dribbles'] == 3

    def test_counts_tackles_with_success_percentage(self):
        """Test tackle counting with success rate calculation."""
        events = [
            create_duel_event(player_id=5503, duel_type_name="Tackle", outcome_id=4),   # Won
            create_duel_event(player_id=5503, duel_type_name="Tackle", outcome_id=15),  # Success
            create_duel_event(player_id=5503, duel_type_name="Tackle", outcome_id=1),   # Lost
            create_duel_event(player_id=5503, duel_type_name="Tackle", outcome_id=16),  # Success In Play
            # Non-tackle duel (should not be counted)
            create_duel_event(player_id=5503, duel_type_name="Aerial Lost", outcome_id=4),
        ]

        result = calculate_player_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        assert result[5503]['tackles'] == 4
        assert result[5503]['tackle_success_rate'] == Decimal('75.00')  # 3/4 = 75%

    def test_counts_interceptions_with_success_rate(self):
        """Test interception counting with CORRECT success logic (outcome IDs 4, 15, 16, 17)."""
        events = [
            create_interception_event(player_id=5503, outcome_id=4),   # Won (success)
            create_interception_event(player_id=5503, outcome_id=15),  # Success
            create_interception_event(player_id=5503, outcome_id=1),   # Lost (failure)
            create_interception_event(player_id=5503, outcome_id=16),  # Success In Play
            create_interception_event(player_id=5503, outcome_id=13),  # Lost In Play (failure)
        ]

        result = calculate_player_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        assert result[5503]['interceptions'] == 5
        assert result[5503]['interception_success_rate'] == Decimal('60.00')  # 3/5 = 60%

    def test_handles_empty_events_list(self):
        """Test that function returns empty dict for empty events list."""
        result = calculate_player_match_statistics_from_events(
            events=[],
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        assert result == {}

    def test_returns_correct_dict_structure(self):
        """Test that returned dict has correct structure with all 17 statistics."""
        events = [
            create_shot_event(player_id=5503, outcome_id=97, statsbomb_xg=0.5),
        ]

        result = calculate_player_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        # Check player key exists
        assert 5503 in result

        # Check all 17 statistics exist (2 required + 15 optional)
        player_stats = result[5503]
        assert 'goals' in player_stats
        assert 'assists' in player_stats
        assert 'expected_goals' in player_stats
        assert 'shots' in player_stats
        assert 'shots_on_target' in player_stats
        assert 'total_dribbles' in player_stats
        assert 'successful_dribbles' in player_stats
        assert 'total_passes' in player_stats
        assert 'completed_passes' in player_stats
        assert 'short_passes' in player_stats
        assert 'long_passes' in player_stats
        assert 'final_third_passes' in player_stats
        assert 'crosses' in player_stats
        assert 'tackles' in player_stats
        assert 'tackle_success_rate' in player_stats
        assert 'interceptions' in player_stats
        assert 'interception_success_rate' in player_stats

    def test_excludes_penalty_shootout_events(self):
        """Test that period 5 (penalty shootout) events are excluded."""
        events = [
            create_shot_event(player_id=5503, outcome_id=97, period=1),  # Regular goal
            create_shot_event(player_id=5503, outcome_id=97, period=5),  # Shootout goal (exclude)
            create_pass_event(player_id=5503, goal_assist=True, period=2),  # Regular assist
            create_pass_event(player_id=5503, goal_assist=True, period=5),  # Shootout assist (exclude)
        ]

        result = calculate_player_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        assert result[5503]['goals'] == 1  # Only period 1 goal
        assert result[5503]['assists'] == 1  # Only period 2 assist

    def test_handles_missing_optional_fields(self):
        """Test robustness when optional fields are missing from events."""
        events = [
            # Shot without statsbomb_xg
            {
                "id": str(uuid4()),
                "type": {"id": 16, "name": "Shot"},
                "team": {"id": 217, "name": "Team"},
                "player": {"id": 5503, "name": "Player"},
                "period": 1,
                "shot": {
                    "outcome": {"id": 100, "name": "Saved"}
                    # Missing statsbomb_xg
                },
                "possession": 1,
                "possession_team": {"id": 217, "name": "Team"},
                "duration": 1.0
            },
            # Pass without outcome (should count as completed)
            {
                "id": str(uuid4()),
                "type": {"id": 30, "name": "Pass"},
                "team": {"id": 217, "name": "Team"},
                "player": {"id": 5503, "name": "Player"},
                "period": 1,
                "location": [50.0, 40.0],
                "pass": {
                    "length": 10.0,
                    "end_location": [60.0, 45.0]
                    # Missing outcome (should be completed)
                },
                "possession": 1,
                "possession_team": {"id": 217, "name": "Team"},
                "duration": 1.0
            },
        ]

        result = calculate_player_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        assert result[5503]['shots'] == 1
        assert result[5503]['expected_goals'] == Decimal('0.00')  # Default to 0
        assert result[5503]['total_passes'] == 1
        assert result[5503]['completed_passes'] == 1  # No outcome means completed

    def test_only_returns_our_team_players(self):
        """Test that only our team's players are included (filtered by team_id)."""
        events = [
            create_shot_event(team_id=217, player_id=5503, outcome_id=97),  # Our team
            create_shot_event(team_id=218, player_id=9999, outcome_id=97),  # Opponent (exclude)
            create_pass_event(team_id=217, player_id=6543, goal_assist=True),  # Our team
            create_pass_event(team_id=218, player_id=8888, goal_assist=True),  # Opponent (exclude)
        ]

        result = calculate_player_match_statistics_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        # Only our team's players should be in result
        assert 5503 in result
        assert 6543 in result
        assert 9999 not in result  # Opponent player
        assert 8888 not in result  # Opponent player
        assert result[5503]['goals'] == 1
        assert result[6543]['assists'] == 1


# =============================================================================
# MAIN FUNCTION TESTS
# =============================================================================

class TestInsertPlayerMatchStatistics:
    """Test insert_player_match_statistics() database function."""

    def test_inserts_statistics_for_starting_11(self, session):
        """Test that function inserts statistics for all starting lineup players."""
        # Given: Match with 11 starting lineup players
        club = Club(coach_id=uuid4(), club_name="Barcelona")
        opponent = OpponentClub(opponent_name="Deportivo Alavés")
        session.add(club)
        session.add(opponent)
        session.commit()

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent.opponent_club_id,
            opponent_name="Deportivo Alavés",
            match_date=date(2017, 8, 26),
            our_score=2,
            opponent_score=0,
            result='W'
        )
        session.add(match)
        session.commit()

        # Create 11 players
        players = []
        for i in range(11):
            player = Player(
                club_id=club.club_id,
                statsbomb_player_id=5000 + i,
                player_name=f"Player {i}",
                jersey_number=i + 1,
                position="Forward",
                invite_code=f"PLR-{5000 + i}"
            )
            session.add(player)
            players.append(player)
        session.commit()

        # Create lineup for all 11 players
        for player in players:
            lineup = MatchLineup(
                match_id=match.match_id,
                player_id=player.player_id,
                team_type='our_team',
                player_name=player.player_name,
                jersey_number=player.jersey_number,
                position="Forward"
            )
            session.add(lineup)
        session.commit()

        # Create events for some players
        events = [
            create_shot_event(player_id=5000, outcome_id=97),  # Player 0 goal
            create_pass_event(player_id=5001, goal_assist=True),  # Player 1 assist
            create_dribble_event(player_id=5002, outcome_name="Complete"),  # Player 2 dribble
        ]

        # When: Insert player match statistics
        result = insert_player_match_statistics(
            db=session,
            match_id=match.match_id,
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        # Then: Should insert 3 records (only players with stats)
        assert result == 3

        # Verify database records
        stats = session.query(PlayerMatchStatistics).filter(
            PlayerMatchStatistics.match_id == match.match_id
        ).all()
        assert len(stats) == 3

    def test_raises_error_if_match_not_found(self, session):
        """Test that function raises ValueError if match_id not found."""
        # Given: Non-existent match_id
        fake_match_id = uuid4()
        events = [create_shot_event(player_id=5503)]

        # When/Then: Should raise ValueError
        with pytest.raises(ValueError, match=f"Match with ID {fake_match_id} not found"):
            insert_player_match_statistics(
                db=session,
                match_id=fake_match_id,
                events=events,
                our_club_statsbomb_id=217,
                opponent_statsbomb_id=218
            )

    def test_raises_error_if_statistics_already_exist(self, session):
        """Test that function raises ValueError if statistics already exist for match."""
        # Given: Match with existing player statistics
        club = Club(coach_id=uuid4(), club_name="Barcelona")
        opponent = OpponentClub(opponent_name="Deportivo Alavés")
        session.add(club)
        session.add(opponent)
        session.commit()

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent.opponent_club_id,
            opponent_name="Deportivo Alavés",
            match_date=date(2017, 8, 26),
            our_score=2,
            opponent_score=0,
            result='W'
        )
        session.add(match)
        session.commit()

        player = Player(
            club_id=club.club_id,
            statsbomb_player_id=5503,
            player_name="Lionel Messi",
            jersey_number=10,
            position="Forward",
            invite_code="MES-5503"
        )
        session.add(player)
        session.commit()

        # Create existing statistics
        existing_stats = PlayerMatchStatistics(
            player_id=player.player_id,
            match_id=match.match_id,
            goals=1,
            assists=0
        )
        session.add(existing_stats)
        session.commit()

        events = [create_shot_event(player_id=5503)]

        # When/Then: Should raise ValueError
        with pytest.raises(ValueError, match=f"Player statistics already exist for match {match.match_id}"):
            insert_player_match_statistics(
                db=session,
                match_id=match.match_id,
                events=events,
                our_club_statsbomb_id=217,
                opponent_statsbomb_id=218
            )

    def test_handles_empty_events_list(self, session):
        """Test that function returns 0 when events list is empty."""
        # Given: Match with no events
        club = Club(coach_id=uuid4(), club_name="Barcelona")
        opponent = OpponentClub(opponent_name="Deportivo Alavés")
        session.add(club)
        session.add(opponent)
        session.commit()

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent.opponent_club_id,
            opponent_name="Deportivo Alavés",
            match_date=date(2017, 8, 26),
            our_score=0,
            opponent_score=0,
            result='D'
        )
        session.add(match)
        session.commit()

        # When: Insert with empty events
        result = insert_player_match_statistics(
            db=session,
            match_id=match.match_id,
            events=[],
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        # Then: Should return 0
        assert result == 0

        # Verify no records inserted
        stats = session.query(PlayerMatchStatistics).filter(
            PlayerMatchStatistics.match_id == match.match_id
        ).all()
        assert len(stats) == 0

    def test_stores_all_statistics_fields_correctly(self, session):
        """Test that all 17 statistics fields are stored correctly in database."""
        # Given: Match with player and comprehensive events
        club = Club(coach_id=uuid4(), club_name="Barcelona")
        opponent = OpponentClub(opponent_name="Deportivo Alavés")
        session.add(club)
        session.add(opponent)
        session.commit()

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent.opponent_club_id,
            opponent_name="Deportivo Alavés",
            match_date=date(2017, 8, 26),
            our_score=2,
            opponent_score=0,
            result='W'
        )
        session.add(match)
        session.commit()

        player = Player(
            club_id=club.club_id,
            statsbomb_player_id=5503,
            player_name="Lionel Messi",
            jersey_number=10,
            position="Forward",
            invite_code="MES-5503"
        )
        session.add(player)
        session.commit()

        lineup = MatchLineup(
            match_id=match.match_id,
            player_id=player.player_id,
            team_type='our_team',
            player_name=player.player_name,
            jersey_number=player.jersey_number,
            position="Forward"
        )
        session.add(lineup)
        session.commit()

        # Create comprehensive events
        events = [
            create_shot_event(player_id=5503, outcome_id=97, statsbomb_xg=0.8),  # Goal
            create_shot_event(player_id=5503, outcome_id=100, statsbomb_xg=0.3),  # Saved
            create_pass_event(player_id=5503, goal_assist=True, pass_length=40.0),  # Assist (long pass)
            create_pass_event(player_id=5503, pass_length=10.0, location=[85.0, 40.0]),  # Short + final third
            create_pass_event(player_id=5503, pass_length=50.0, is_cross=True),  # Long + cross
            create_dribble_event(player_id=5503, outcome_name="Complete"),  # Successful dribble
            create_dribble_event(player_id=5503, outcome_name="Incomplete"),  # Failed dribble
            create_duel_event(player_id=5503, duel_type_name="Tackle", outcome_id=4),  # Successful tackle
            create_duel_event(player_id=5503, duel_type_name="Tackle", outcome_id=1),  # Failed tackle
            create_interception_event(player_id=5503, outcome_id=15),  # Successful interception
        ]

        # When: Insert player statistics
        result = insert_player_match_statistics(
            db=session,
            match_id=match.match_id,
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        # Then: Verify all fields stored correctly
        assert result == 1
        stats = session.query(PlayerMatchStatistics).filter(
            PlayerMatchStatistics.player_id == player.player_id,
            PlayerMatchStatistics.match_id == match.match_id
        ).first()

        assert stats.goals == 1
        assert stats.assists == 1
        assert stats.expected_goals == Decimal('1.1')  # 0.8 + 0.3
        assert stats.shots == 2
        assert stats.shots_on_target == 2
        assert stats.total_passes == 3
        assert stats.completed_passes == 3  # All completed (no outcome)
        assert stats.short_passes == 1
        assert stats.long_passes == 2
        assert stats.final_third_passes == 1
        assert stats.crosses == 1
        assert stats.total_dribbles == 2
        assert stats.successful_dribbles == 1
        assert stats.tackles == 2
        assert stats.tackle_success_rate == Decimal('50.00')  # 1/2 = 50%
        assert stats.interceptions == 1
        assert stats.interception_success_rate == Decimal('100.00')  # 1/1 = 100%

    def test_commits_transaction_successfully(self, session):
        """Test that function commits transaction and persists data."""
        # Given: Match with player
        club = Club(coach_id=uuid4(), club_name="Barcelona")
        opponent = OpponentClub(opponent_name="Deportivo Alavés")
        session.add(club)
        session.add(opponent)
        session.commit()

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent.opponent_club_id,
            opponent_name="Deportivo Alavés",
            match_date=date(2017, 8, 26),
            our_score=1,
            opponent_score=0,
            result='W'
        )
        session.add(match)
        session.commit()

        player = Player(
            club_id=club.club_id,
            statsbomb_player_id=5503,
            player_name="Lionel Messi",
            jersey_number=10,
            position="Forward",
            invite_code="MES-5503"
        )
        session.add(player)
        session.commit()

        lineup = MatchLineup(
            match_id=match.match_id,
            player_id=player.player_id,
            team_type='our_team',
            player_name=player.player_name,
            jersey_number=player.jersey_number,
            position="Forward"
        )
        session.add(lineup)
        session.commit()

        events = [create_shot_event(player_id=5503, outcome_id=97)]

        # When: Insert statistics
        insert_player_match_statistics(
            db=session,
            match_id=match.match_id,
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        # Then: Data should be persisted (query in new session context)
        stats = session.query(PlayerMatchStatistics).filter(
            PlayerMatchStatistics.match_id == match.match_id
        ).first()
        assert stats is not None
        assert stats.goals == 1

    def test_only_inserts_for_starting_lineup_players(self, session):
        """Test that function only inserts stats for players in starting lineup."""
        # Given: Match with lineup and events for both lineup and non-lineup players
        club = Club(coach_id=uuid4(), club_name="Barcelona")
        opponent = OpponentClub(opponent_name="Deportivo Alavés")
        session.add(club)
        session.add(opponent)
        session.commit()

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent.opponent_club_id,
            opponent_name="Deportivo Alavés",
            match_date=date(2017, 8, 26),
            our_score=2,
            opponent_score=0,
            result='W'
        )
        session.add(match)
        session.commit()

        # Create 2 players: one in lineup, one substitute (not in lineup)
        player_in_lineup = Player(
            club_id=club.club_id,
            statsbomb_player_id=5503,
            player_name="Lineup Player",
            jersey_number=10,
            position="Forward",
            invite_code="LIN-5503"
        )
        player_substitute = Player(
            club_id=club.club_id,
            statsbomb_player_id=6543,
            player_name="Substitute Player",
            jersey_number=7,
            position="Midfielder",
            invite_code="SUB-6543"
        )
        session.add(player_in_lineup)
        session.add(player_substitute)
        session.commit()

        # Only add one player to lineup (not the substitute)
        lineup = MatchLineup(
            match_id=match.match_id,
            player_id=player_in_lineup.player_id,
            team_type='our_team',
            player_name=player_in_lineup.player_name,
            jersey_number=player_in_lineup.jersey_number,
            position="Forward"
        )
        session.add(lineup)
        session.commit()

        # Events for both players
        events = [
            create_shot_event(player_id=5503, outcome_id=97),  # Lineup player
            create_shot_event(player_id=6543, outcome_id=97),  # Substitute (not in lineup)
        ]

        # When: Insert statistics
        result = insert_player_match_statistics(
            db=session,
            match_id=match.match_id,
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        # Then: Should only insert for lineup player
        assert result == 1

        stats = session.query(PlayerMatchStatistics).filter(
            PlayerMatchStatistics.match_id == match.match_id
        ).all()
        assert len(stats) == 1
        assert stats[0].player_id == player_in_lineup.player_id

    def test_excludes_penalty_shootout_events(self, session):
        """Test that function excludes period 5 (penalty shootout) events."""
        # Given: Match with regular and shootout events
        club = Club(coach_id=uuid4(), club_name="Barcelona")
        opponent = OpponentClub(opponent_name="Deportivo Alavés")
        session.add(club)
        session.add(opponent)
        session.commit()

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent.opponent_club_id,
            opponent_name="Deportivo Alavés",
            match_date=date(2017, 8, 26),
            our_score=2,
            opponent_score=2,
            result='D'
        )
        session.add(match)
        session.commit()

        player = Player(
            club_id=club.club_id,
            statsbomb_player_id=5503,
            player_name="Lionel Messi",
            jersey_number=10,
            position="Forward",
            invite_code="MES-5503"
        )
        session.add(player)
        session.commit()

        lineup = MatchLineup(
            match_id=match.match_id,
            player_id=player.player_id,
            team_type='our_team',
            player_name=player.player_name,
            jersey_number=player.jersey_number,
            position="Forward"
        )
        session.add(lineup)
        session.commit()

        # Events: 1 regular goal + 1 shootout goal
        events = [
            create_shot_event(player_id=5503, outcome_id=97, period=1),  # Regular (include)
            create_shot_event(player_id=5503, outcome_id=97, period=5),  # Shootout (exclude)
            create_pass_event(player_id=5503, goal_assist=True, period=2),  # Regular (include)
            create_pass_event(player_id=5503, goal_assist=True, period=5),  # Shootout (exclude)
        ]

        # When: Insert statistics
        result = insert_player_match_statistics(
            db=session,
            match_id=match.match_id,
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=218
        )

        # Then: Should only count regular period events
        assert result == 1

        stats = session.query(PlayerMatchStatistics).filter(
            PlayerMatchStatistics.player_id == player.player_id,
            PlayerMatchStatistics.match_id == match.match_id
        ).first()

        assert stats.goals == 1  # Only regular goal
        assert stats.assists == 1  # Only regular assist
