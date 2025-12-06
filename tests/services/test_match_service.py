"""
Tests for match service.
"""

import pytest
from uuid import UUID
from datetime import date

from app.services.match_service import count_goals_from_events, create_match_record
from app.models.club import Club
from app.models.opponent_club import OpponentClub
from app.models.match import Match


def create_shot_event(
    event_id: str,
    team_id: int,
    team_name: str,
    outcome_id: int,
    outcome_name: str
) -> dict:
    """Helper to create a Shot event for testing."""
    return {
        "id": event_id,
        "type": {"id": 16, "name": "Shot"},
        "team": {"id": team_id, "name": team_name},
        "shot": {
            "outcome": {"id": outcome_id, "name": outcome_name}
        }
    }


def create_pass_event(event_id: str, team_id: int) -> dict:
    """Helper to create a Pass event (not a shot)."""
    return {
        "id": event_id,
        "type": {"id": 30, "name": "Pass"},
        "team": {"id": team_id, "name": "Some Team"}
    }


class TestCountGoalsFromEvents:
    """Test count_goals_from_events helper function."""

    def test_both_teams_scoring(self):
        """Test counting goals when both teams score."""
        events = [
            # Argentina goals (team_id: 779)
            create_shot_event("goal-1", 779, "Argentina", 97, "Goal"),
            create_shot_event("goal-2", 779, "Argentina", 97, "Goal"),
            # Australia goal (team_id: 792)
            create_shot_event("goal-3", 792, "Australia", 97, "Goal"),
            # Non-goal shots
            create_shot_event("miss-1", 779, "Argentina", 101, "Off Target"),
            create_shot_event("save-1", 792, "Australia", 100, "Saved"),
            # Non-shot events
            create_pass_event("pass-1", 779),
            create_pass_event("pass-2", 792)
        ]

        result = count_goals_from_events(
            events=events,
            our_club_statsbomb_team_id=779,
            opponent_statsbomb_team_id=792
        )

        assert result['our_goals'] == 2
        assert result['opponent_goals'] == 1

    def test_no_goals_draw(self):
        """Test counting when no goals (0-0 draw)."""
        events = [
            # Only non-goal shots
            create_shot_event("miss-1", 779, "Argentina", 101, "Off Target"),
            create_shot_event("save-1", 792, "Australia", 100, "Saved"),
            create_shot_event("block-1", 779, "Argentina", 102, "Blocked"),
            # Non-shot events
            create_pass_event("pass-1", 779),
            create_pass_event("pass-2", 792)
        ]

        result = count_goals_from_events(
            events=events,
            our_club_statsbomb_team_id=779,
            opponent_statsbomb_team_id=792
        )

        assert result['our_goals'] == 0
        assert result['opponent_goals'] == 0

    def test_only_our_team_scoring(self):
        """Test counting when only our team scores."""
        events = [
            # Only our goals
            create_shot_event("goal-1", 779, "Argentina", 97, "Goal"),
            create_shot_event("goal-2", 779, "Argentina", 97, "Goal"),
            create_shot_event("goal-3", 779, "Argentina", 97, "Goal"),
            # Opponent misses
            create_shot_event("miss-1", 792, "Australia", 101, "Off Target"),
        ]

        result = count_goals_from_events(
            events=events,
            our_club_statsbomb_team_id=779,
            opponent_statsbomb_team_id=792
        )

        assert result['our_goals'] == 3
        assert result['opponent_goals'] == 0

    def test_only_opponent_scoring(self):
        """Test counting when only opponent scores."""
        events = [
            # Only opponent goals
            create_shot_event("goal-1", 792, "Australia", 97, "Goal"),
            create_shot_event("goal-2", 792, "Australia", 97, "Goal"),
            # Our misses
            create_shot_event("miss-1", 779, "Argentina", 101, "Off Target"),
        ]

        result = count_goals_from_events(
            events=events,
            our_club_statsbomb_team_id=779,
            opponent_statsbomb_team_id=792
        )

        assert result['our_goals'] == 0
        assert result['opponent_goals'] == 2

    def test_empty_events(self):
        """Test with empty events array."""
        result = count_goals_from_events(
            events=[],
            our_club_statsbomb_team_id=779,
            opponent_statsbomb_team_id=792
        )

        assert result['our_goals'] == 0
        assert result['opponent_goals'] == 0

    def test_excludes_penalty_shootout_goals(self):
        """Test that penalty shootout goals (period 5) are NOT counted."""
        events = [
            # Regular time goals (periods 1-4) - should be counted
            {
                "id": "goal-1",
                "period": 1,
                "type": {"id": 16, "name": "Shot"},
                "team": {"id": 779, "name": "Argentina"},
                "shot": {"outcome": {"id": 97, "name": "Goal"}}
            },
            {
                "id": "goal-2",
                "period": 2,
                "type": {"id": 16, "name": "Shot"},
                "team": {"id": 792, "name": "Australia"},
                "shot": {"outcome": {"id": 97, "name": "Goal"}}
            },
            # Penalty shootout goals (period 5) - should NOT be counted
            {
                "id": "penalty-1",
                "period": 5,
                "type": {"id": 16, "name": "Shot"},
                "team": {"id": 779, "name": "Argentina"},
                "shot": {
                    "type": {"id": 88, "name": "Penalty"},
                    "outcome": {"id": 97, "name": "Goal"}
                }
            },
            {
                "id": "penalty-2",
                "period": 5,
                "type": {"id": 16, "name": "Shot"},
                "team": {"id": 792, "name": "Australia"},
                "shot": {
                    "type": {"id": 88, "name": "Penalty"},
                    "outcome": {"id": 97, "name": "Goal"}
                }
            },
            {
                "id": "penalty-3",
                "period": 5,
                "type": {"id": 16, "name": "Shot"},
                "team": {"id": 779, "name": "Argentina"},
                "shot": {
                    "type": {"id": 88, "name": "Penalty"},
                    "outcome": {"id": 97, "name": "Goal"}
                }
            }
        ]

        result = count_goals_from_events(
            events=events,
            our_club_statsbomb_team_id=779,
            opponent_statsbomb_team_id=792
        )

        # Only regular time goals should be counted (1 each)
        # Penalty shootout goals should be excluded (3 total in period 5)
        assert result['our_goals'] == 1  # NOT 2 (excludes penalty shootout)
        assert result['opponent_goals'] == 1  # NOT 2 (excludes penalty shootout)


class TestCreateMatchRecord:
    """Test create_match_record function."""

    def test_create_match_win_result(self, session):
        """Test creating match with Win result (our_score > opponent_score)."""
        # Given: Club and opponent club exist
        club = Club(
            coach_id="coach-id-placeholder",  # UUID string
            club_name="Test FC",
            statsbomb_team_id=779
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(
            statsbomb_team_id=792,
            opponent_name="Opponent FC"
        )
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        # Given: Events with 2 goals for us, 1 for opponent (matches scores)
        events = [
            create_shot_event("goal-1", 779, "Test FC", 97, "Goal"),
            create_shot_event("goal-2", 779, "Test FC", 97, "Goal"),
            create_shot_event("goal-3", 792, "Opponent FC", 97, "Goal")
        ]

        # When: Create match with our_score=2, opponent_score=1
        match_id = create_match_record(
            db=session,
            club_id=club.club_id,
            opponent_club_id=opponent_club.opponent_club_id,
            match_date="2024-11-18",
            our_score=2,
            opponent_score=1,
            opponent_name="Opponent FC",
            events=events
        )

        # Then: Match created with Win result
        assert isinstance(match_id, (UUID, str))

        match = session.query(Match).filter(Match.match_id == match_id).first()
        assert match is not None
        assert match.club_id == club.club_id
        assert match.opponent_club_id == opponent_club.opponent_club_id
        assert match.our_score == 2
        assert match.opponent_score == 1
        assert match.result == 'W'  # Win
        assert match.opponent_name == "Opponent FC"

    def test_create_match_draw_result(self, session):
        """Test creating match with Draw result (our_score == opponent_score)."""
        # Given: Club and opponent club exist
        club = Club(
            coach_id="coach-id-placeholder",
            club_name="Test FC",
            statsbomb_team_id=779
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(
            statsbomb_team_id=792,
            opponent_name="Opponent FC"
        )
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        # Given: Events with 1 goal for each team
        events = [
            create_shot_event("goal-1", 779, "Test FC", 97, "Goal"),
            create_shot_event("goal-2", 792, "Opponent FC", 97, "Goal")
        ]

        # When: Create match with our_score=1, opponent_score=1
        match_id = create_match_record(
            db=session,
            club_id=club.club_id,
            opponent_club_id=opponent_club.opponent_club_id,
            match_date="2024-11-18",
            our_score=1,
            opponent_score=1,
            opponent_name="Opponent FC",
            events=events
        )

        # Then: Match created with Draw result
        match = session.query(Match).filter(Match.match_id == match_id).first()
        assert match.result == 'D'  # Draw

    def test_create_match_loss_result(self, session):
        """Test creating match with Loss result (our_score < opponent_score)."""
        # Given: Club and opponent club exist
        club = Club(
            coach_id="coach-id-placeholder",
            club_name="Test FC",
            statsbomb_team_id=779
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(
            statsbomb_team_id=792,
            opponent_name="Opponent FC"
        )
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        # Given: Events with 1 goal for us, 3 for opponent
        events = [
            create_shot_event("goal-1", 779, "Test FC", 97, "Goal"),
            create_shot_event("goal-2", 792, "Opponent FC", 97, "Goal"),
            create_shot_event("goal-3", 792, "Opponent FC", 97, "Goal"),
            create_shot_event("goal-4", 792, "Opponent FC", 97, "Goal")
        ]

        # When: Create match with our_score=1, opponent_score=3
        match_id = create_match_record(
            db=session,
            club_id=club.club_id,
            opponent_club_id=opponent_club.opponent_club_id,
            match_date="2024-11-18",
            our_score=1,
            opponent_score=3,
            opponent_name="Opponent FC",
            events=events
        )

        # Then: Match created with Loss result
        match = session.query(Match).filter(Match.match_id == match_id).first()
        assert match.result == 'L'  # Loss

    def test_score_validation_mismatch_error(self, session):
        """Test error when user scores don't match event data."""
        # Given: Club and opponent club exist
        club = Club(
            coach_id="coach-id-placeholder",
            club_name="Test FC",
            statsbomb_team_id=779
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(
            statsbomb_team_id=792,
            opponent_name="Opponent FC"
        )
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        # Given: Events show 2-1, but user claims 3-1
        events = [
            create_shot_event("goal-1", 779, "Test FC", 97, "Goal"),
            create_shot_event("goal-2", 779, "Test FC", 97, "Goal"),
            create_shot_event("goal-3", 792, "Opponent FC", 97, "Goal")
        ]

        # When/Then: Should raise ValueError
        with pytest.raises(ValueError, match="Score mismatch"):
            create_match_record(
                db=session,
                club_id=club.club_id,
                opponent_club_id=opponent_club.opponent_club_id,
                match_date="2024-11-18",
                our_score=3,  # Wrong! Should be 2
                opponent_score=1,
                opponent_name="Opponent FC",
                events=events
            )

    def test_score_validation_success(self, session):
        """Test success when scores match event data exactly."""
        # Given: Club and opponent club exist
        club = Club(
            coach_id="coach-id-placeholder",
            club_name="Test FC",
            statsbomb_team_id=779
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(
            statsbomb_team_id=792,
            opponent_name="Opponent FC"
        )
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        # Given: Events show 2-1, user also says 2-1
        events = [
            create_shot_event("goal-1", 779, "Test FC", 97, "Goal"),
            create_shot_event("goal-2", 779, "Test FC", 97, "Goal"),
            create_shot_event("goal-3", 792, "Opponent FC", 97, "Goal")
        ]

        # When: Create match with correct scores
        match_id = create_match_record(
            db=session,
            club_id=club.club_id,
            opponent_club_id=opponent_club.opponent_club_id,
            match_date="2024-11-18",
            our_score=2,  # Matches event data
            opponent_score=1,  # Matches event data
            opponent_name="Opponent FC",
            events=events
        )

        # Then: Match created successfully
        assert isinstance(match_id, (UUID, str))
        match = session.query(Match).filter(Match.match_id == match_id).first()
        assert match is not None
