"""
Tests for goal service functions.

Tests the extraction and storage of goal events from StatsBomb data.
"""

import pytest
from uuid import uuid4, UUID
from app.services.goal_service import parse_goals_from_events, insert_goals
from app.models.match import Match
from app.models.club import Club
from app.models.opponent_club import OpponentClub
from app.models.goal import Goal
from datetime import date


# Test fixtures
def create_goal_event(
    team_id: int = 217,
    team_name: str = "Barcelona",
    player_id: int = 5503,
    player_name: str = "Lionel Andrés Messi Cuccittini",
    minute: int = 12,
    second: int = 34,
    period: int = 1
):
    """Create minimal Shot event with Goal outcome."""
    return {
        "id": str(uuid4()),
        "index": 100,
        "period": period,
        "minute": minute,
        "second": second,
        "type": {"id": 16, "name": "Shot"},
        "possession_team": {"id": team_id, "name": team_name},
        "team": {"id": team_id, "name": team_name},
        "player": {"id": player_id, "name": player_name},
        "position": {"id": 24, "name": "Center Forward"},
        "shot": {
            "outcome": {"id": 97, "name": "Goal"},
            "statsbomb_xg": 0.35
        }
    }


def create_non_goal_shot(
    team_id: int = 217,
    outcome_id: int = 100,
    outcome_name: str = "Saved"
):
    """Create Shot event with non-goal outcome (Saved, Blocked, etc.)."""
    return {
        "id": str(uuid4()),
        "index": 101,
        "period": 1,
        "minute": 15,
        "second": 45,
        "type": {"id": 16, "name": "Shot"},
        "team": {"id": team_id, "name": "Barcelona"},
        "player": {"id": 5503, "name": "Lionel Messi"},
        "shot": {
            "outcome": {"id": outcome_id, "name": outcome_name},
            "statsbomb_xg": 0.15
        }
    }


def create_penalty_shootout_goal(team_id: int = 217):
    """Create Shot event with Goal outcome in penalty shootout (period 5)."""
    return {
        "id": str(uuid4()),
        "index": 500,
        "period": 5,  # Penalty shootout
        "minute": 120,
        "second": 0,
        "type": {"id": 16, "name": "Shot"},
        "team": {"id": team_id, "name": "Barcelona"},
        "player": {"id": 5503, "name": "Lionel Messi"},
        "shot": {
            "outcome": {"id": 97, "name": "Goal"},
            "statsbomb_xg": 0.78
        }
    }


class TestParseGoalsFromEvents:
    """Test parse_goals_from_events helper function."""

    def test_extracts_goals_from_shot_events(self):
        """Test that function extracts goals from Shot events with outcome 97 (Goal)."""
        # Given: Events with 2 goals and other events
        events = [
            create_goal_event(team_id=217, player_name="Player 1", minute=10, second=30),
            create_goal_event(team_id=206, player_name="Player 2", minute=45, second=15),
            create_non_goal_shot(team_id=217, outcome_id=100, outcome_name="Saved"),
            {"type": {"id": 30, "name": "Pass"}}  # Non-shot event
        ]

        # When: Parse goals
        result = parse_goals_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Should extract 2 goals
        assert len(result) == 2
        assert result[0]['scorer_name'] == "Player 1"
        assert result[1]['scorer_name'] == "Player 2"

    def test_excludes_non_goal_shots(self):
        """Test that function excludes Shot events without Goal outcome."""
        # Given: Events with saved/blocked shots but no goals
        events = [
            create_non_goal_shot(team_id=217, outcome_id=100, outcome_name="Saved"),
            create_non_goal_shot(team_id=217, outcome_id=101, outcome_name="Blocked"),
            create_non_goal_shot(team_id=217, outcome_id=102, outcome_name="Off Target"),
            create_non_goal_shot(team_id=217, outcome_id=103, outcome_name="Post")
        ]

        # When: Parse goals
        result = parse_goals_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Should find 0 goals
        assert len(result) == 0

    def test_excludes_penalty_shootout_goals(self):
        """Test that function excludes goals from penalty shootout (period 5)."""
        # Given: Mix of regular goals and penalty shootout goals
        events = [
            create_goal_event(team_id=217, period=1, minute=10),  # Regular time
            create_goal_event(team_id=206, period=2, minute=60),  # Regular time
            create_penalty_shootout_goal(team_id=217),  # Penalty shootout - EXCLUDE
            create_penalty_shootout_goal(team_id=206)   # Penalty shootout - EXCLUDE
        ]

        # When: Parse goals
        result = parse_goals_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Should only extract 2 regular goals (exclude period 5)
        assert len(result) == 2
        assert all(goal['minute'] < 120 for goal in result)  # Not penalty shootout timing

    def test_extracts_all_fields_correctly(self):
        """Test that function correctly extracts scorer_name, minute, second, is_our_goal."""
        # Given: Goal events with all fields
        events = [
            create_goal_event(
                team_id=217,
                player_name="Lionel Andrés Messi Cuccittini",
                minute=12,
                second=34,
                period=1
            ),
            create_goal_event(
                team_id=206,
                player_name="Opponent Player",
                minute=78,
                second=56,
                period=2
            )
        ]

        # When: Parse goals
        result = parse_goals_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: First goal (our team)
        assert result[0]['scorer_name'] == "Lionel Andrés Messi Cuccittini"
        assert result[0]['minute'] == 12
        assert result[0]['second'] == 34
        assert result[0]['is_our_goal'] is True

        # Second goal (opponent)
        assert result[1]['scorer_name'] == "Opponent Player"
        assert result[1]['minute'] == 78
        assert result[1]['second'] == 56
        assert result[1]['is_our_goal'] is False

    def test_handles_missing_player(self):
        """Test that function handles goal events without player field (sets 'Unknown')."""
        # Given: Goal event without player field
        goal_without_player = {
            "id": str(uuid4()),
            "period": 1,
            "minute": 25,
            "second": 10,
            "type": {"id": 16, "name": "Shot"},
            "team": {"id": 217, "name": "Barcelona"},
            # No "player" field
            "shot": {
                "outcome": {"id": 97, "name": "Goal"}
            }
        }

        events = [goal_without_player]

        # When: Parse goals
        result = parse_goals_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Should use "Unknown" for scorer_name
        assert len(result) == 1
        assert result[0]['scorer_name'] == "Unknown"
        assert result[0]['minute'] == 25
        assert result[0]['second'] == 10

    def test_handles_missing_second(self):
        """Test that function handles goal events without second field (returns None)."""
        # Given: Goal event without second field
        goal_without_second = {
            "id": str(uuid4()),
            "period": 1,
            "minute": 30,
            # No "second" field
            "type": {"id": 16, "name": "Shot"},
            "team": {"id": 217, "name": "Barcelona"},
            "player": {"id": 5503, "name": "Lionel Messi"},
            "shot": {
                "outcome": {"id": 97, "name": "Goal"}
            }
        }

        events = [goal_without_second]

        # When: Parse goals
        result = parse_goals_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Should have None for second
        assert len(result) == 1
        assert result[0]['scorer_name'] == "Lionel Messi"
        assert result[0]['minute'] == 30
        assert result[0]['second'] is None

    def test_determines_is_our_goal_correctly(self):
        """Test that function correctly determines is_our_goal for both teams."""
        # Given: Goals from both teams
        events = [
            create_goal_event(team_id=217, player_name="Our Player 1", minute=10),
            create_goal_event(team_id=206, player_name="Opp Player 1", minute=20),
            create_goal_event(team_id=217, player_name="Our Player 2", minute=30),
            create_goal_event(team_id=206, player_name="Opp Player 2", minute=40)
        ]

        # When: Parse goals
        result = parse_goals_from_events(
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Verify is_our_goal for each
        assert len(result) == 4
        assert result[0]['is_our_goal'] is True   # team_id=217 (our team)
        assert result[1]['is_our_goal'] is False  # team_id=206 (opponent)
        assert result[2]['is_our_goal'] is True   # team_id=217 (our team)
        assert result[3]['is_our_goal'] is False  # team_id=206 (opponent)


class TestInsertGoals:
    """Test insert_goals main database function."""

    def test_inserts_goals_into_database(self, session):
        """Test that function inserts goal records into database."""
        # Given: Match and goal events
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

        events = [
            create_goal_event(team_id=217, player_name="Player 1", minute=10, second=30),
            create_goal_event(team_id=206, player_name="Player 2", minute=45, second=15)
        ]

        # When: Insert goals
        from app.services.goal_service import insert_goals
        result = insert_goals(
            db=session,
            match_id=match.match_id,
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Should insert 2 goals
        assert result == 2

        # Verify database records
        goals = session.query(Goal).filter(Goal.match_id == match.match_id).all()
        assert len(goals) == 2
        assert goals[0].scorer_name == "Player 1"
        assert goals[0].minute == 10
        assert goals[0].second == 30
        assert goals[0].is_our_goal is True
        assert goals[1].scorer_name == "Player 2"
        assert goals[1].minute == 45
        assert goals[1].second == 15
        assert goals[1].is_our_goal is False

    def test_returns_zero_for_no_goals(self, session):
        """Test that function returns 0 when no goals in events (valid scenario)."""
        # Given: Match with no goal events
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

        # Events with only non-goal shots
        events = [
            create_non_goal_shot(team_id=217, outcome_id=100, outcome_name="Saved"),
            create_non_goal_shot(team_id=206, outcome_id=101, outcome_name="Blocked")
        ]

        # When: Insert goals
        from app.services.goal_service import insert_goals
        result = insert_goals(
            db=session,
            match_id=match.match_id,
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Should return 0
        assert result == 0

        # Verify no goals in database
        goals = session.query(Goal).filter(Goal.match_id == match.match_id).all()
        assert len(goals) == 0

    def test_raises_error_if_match_not_found(self, session):
        """Test that function raises ValueError if match_id not found."""
        # Given: Non-existent match_id
        fake_match_id = uuid4()
        events = [create_goal_event(team_id=217, minute=10)]

        # When/Then: Should raise ValueError
        from app.services.goal_service import insert_goals
        with pytest.raises(ValueError, match=f"Match with ID {fake_match_id} not found"):
            insert_goals(
                db=session,
                match_id=fake_match_id,
                events=events,
                our_club_statsbomb_id=217,
                opponent_statsbomb_id=206
            )

    def test_excludes_penalty_shootout_goals(self, session):
        """Test that function excludes penalty shootout goals (period 5)."""
        # Given: Match and mix of regular + penalty shootout goals
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

        events = [
            create_goal_event(team_id=217, period=1, minute=10),  # Regular - INCLUDE
            create_goal_event(team_id=206, period=2, minute=60),  # Regular - INCLUDE
            create_penalty_shootout_goal(team_id=217),  # Period 5 - EXCLUDE
            create_penalty_shootout_goal(team_id=206)   # Period 5 - EXCLUDE
        ]

        # When: Insert goals
        from app.services.goal_service import insert_goals
        result = insert_goals(
            db=session,
            match_id=match.match_id,
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Should only insert 2 regular goals (exclude period 5)
        assert result == 2

        # Verify only regular goals in database
        goals = session.query(Goal).filter(Goal.match_id == match.match_id).all()
        assert len(goals) == 2
        assert all(goal.minute < 120 for goal in goals)  # Not penalty shootout timing

    def test_handles_missing_player_field(self, session):
        """Test that function handles goals without player field (uses 'Unknown')."""
        # Given: Match and goal without player field
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

        goal_without_player = {
            "id": str(uuid4()),
            "period": 1,
            "minute": 25,
            "second": 10,
            "type": {"id": 16, "name": "Shot"},
            "team": {"id": 217, "name": "Barcelona"},
            # No "player" field
            "shot": {
                "outcome": {"id": 97, "name": "Goal"}
            }
        }

        events = [goal_without_player]

        # When: Insert goals
        from app.services.goal_service import insert_goals
        result = insert_goals(
            db=session,
            match_id=match.match_id,
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Should insert 1 goal with "Unknown" scorer
        assert result == 1

        # Verify "Unknown" scorer in database
        goal = session.query(Goal).filter(Goal.match_id == match.match_id).first()
        assert goal.scorer_name == "Unknown"
        assert goal.minute == 25
        assert goal.second == 10

    def test_handles_missing_second_field(self, session):
        """Test that function handles goals without second field (stores None)."""
        # Given: Match and goal without second field
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

        goal_without_second = {
            "id": str(uuid4()),
            "period": 1,
            "minute": 30,
            # No "second" field
            "type": {"id": 16, "name": "Shot"},
            "team": {"id": 217, "name": "Barcelona"},
            "player": {"id": 5503, "name": "Lionel Messi"},
            "shot": {
                "outcome": {"id": 97, "name": "Goal"}
            }
        }

        events = [goal_without_second]

        # When: Insert goals
        from app.services.goal_service import insert_goals
        result = insert_goals(
            db=session,
            match_id=match.match_id,
            events=events,
            our_club_statsbomb_id=217,
            opponent_statsbomb_id=206
        )

        # Then: Should insert 1 goal with None for second
        assert result == 1

        # Verify None for second in database
        goal = session.query(Goal).filter(Goal.match_id == match.match_id).first()
        assert goal.scorer_name == "Lionel Messi"
        assert goal.minute == 30
        assert goal.second is None
