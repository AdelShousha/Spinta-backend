"""
Tests for event service functions.

Tests the storage of Pass, Shot, and Dribble events from StatsBomb data.
"""

import pytest
from uuid import uuid4, UUID
from app.services.event_service import parse_events_for_storage, insert_events
from app.models.match import Match
from app.models.club import Club
from app.models.opponent_club import OpponentClub
from app.models.event import Event
from datetime import date


# Test fixtures
def create_shot_event(
    player_id: int = 5503,
    player_name: str = "Lionel Andrés Messi Cuccittini",
    team_id: int = 217,
    team_name: str = "Barcelona",
    minute: int = 2,
    second: int = 29,
    period: int = 1,
    position_name: str = "Left Center Forward"
):
    """Create minimal Shot event for testing."""
    return {
        "id": str(uuid4()),
        "index": 100,
        "minute": minute,
        "second": second,
        "type": {"id": 16, "name": "Shot"},
        "team": {"id": team_id, "name": team_name},
        "player": {"id": player_id, "name": player_name},
        "position": {"id": 24, "name": position_name},
        "period": period,
        "shot": {
            "statsbomb_xg": 0.024542088,
            "outcome": {"id": 100, "name": "Saved"}
        }
    }


def create_pass_event(
    player_id: int = 6581,
    player_name: str = "Jonathan Rodríguez Menéndez",
    team_id: int = 206,
    team_name: str = "Deportivo Alavés",
    minute: int = 0,
    second: int = 0,
    period: int = 1,
    position_name: str = "Left Midfield"
):
    """Create minimal Pass event for testing."""
    return {
        "id": str(uuid4()),
        "index": 5,
        "minute": minute,
        "second": second,
        "type": {"id": 30, "name": "Pass"},
        "team": {"id": team_id, "name": team_name},
        "player": {"id": player_id, "name": player_name},
        "position": {"id": 16, "name": position_name},
        "period": period,
        "pass": {
            "recipient": {"id": 12345, "name": "Recipient Name"},
            "length": 13.364505,
            "angle": 2.907503
        }
    }


def create_dribble_event(
    player_id: int = 2995,
    player_name: str = "Ángel Fabián Di María Hernández",
    team_id: int = 779,
    team_name: str = "Argentina",
    minute: int = 4,
    second: int = 8,
    period: int = 1,
    position_name: str = "Left Wing"
):
    """Create minimal Dribble event for testing."""
    return {
        "id": str(uuid4()),
        "index": 155,
        "minute": minute,
        "second": second,
        "type": {"id": 14, "name": "Dribble"},
        "team": {"id": team_id, "name": team_name},
        "player": {"id": player_id, "name": player_name},
        "position": {"id": 21, "name": position_name},
        "period": period,
        "dribble": {
            "outcome": {"id": 9, "name": "Incomplete"}
        }
    }


def create_other_event(event_type_id: int = 18, event_type_name: str = "Half Start"):
    """Create non-Pass/Shot/Dribble event for testing filtering."""
    return {
        "id": str(uuid4()),
        "index": 1,
        "minute": 0,
        "second": 0,
        "type": {"id": event_type_id, "name": event_type_name},
        "team": {"id": 217, "name": "Barcelona"},
        "period": 1
        # Note: No "player" or "position" field
    }


class TestParseEventsForStorage:
    """Test parse_events_for_storage helper function."""

    def test_filters_only_three_event_types(self):
        """Test that function filters only Pass (30), Shot (16), and Dribble (14) events."""
        # Given: Mix of event types
        events = [
            create_pass_event(),
            create_shot_event(),
            create_dribble_event(),
            create_other_event(18, "Half Start"),
            create_other_event(35, "Starting XI"),
            create_other_event(19, "Substitution"),
            create_pass_event(minute=5),
            create_shot_event(minute=10)
        ]

        # When: Parse events
        result = parse_events_for_storage(events)

        # Then: Only 5 events match filter (3 pass/shot/dribble types)
        assert result['total_events'] == 8
        assert result['filtered_count'] == 5  # 2 pass, 2 shot, 1 dribble

    def test_extracts_all_fields_correctly(self):
        """Test that function correctly extracts all fields from valid events."""
        # Given: Events with all fields present
        events = [
            create_shot_event(
                player_id=5503,
                player_name="Lionel Andrés Messi Cuccittini",
                team_id=217,
                team_name="Barcelona",
                minute=2,
                second=29,
                period=1,
                position_name="Left Center Forward"
            ),
            create_pass_event(
                player_id=6581,
                player_name="Jonathan Rodríguez Menéndez",
                team_id=206,
                team_name="Deportivo Alavés",
                minute=0,
                second=0,
                period=1,
                position_name="Left Midfield"
            ),
            create_dribble_event(
                player_id=2995,
                player_name="Ángel Fabián Di María Hernández",
                team_id=779,
                team_name="Argentina",
                minute=4,
                second=8,
                period=1,
                position_name="Left Wing"
            )
        ]

        # When: Parse events
        result = parse_events_for_storage(events)

        # Then: Verify shot extraction
        assert result['first_shot'] is not None
        shot_extracted = result['first_shot']['extracted']
        assert shot_extracted['player_name'] == "Lionel Andrés Messi Cuccittini"
        assert shot_extracted['statsbomb_player_id'] == 5503
        assert shot_extracted['team_name'] == "Barcelona"
        assert shot_extracted['statsbomb_team_id'] == 217
        assert shot_extracted['event_type_name'] == "Shot"
        assert shot_extracted['position_name'] == "Left Center Forward"
        assert shot_extracted['minute'] == 2
        assert shot_extracted['second'] == 29
        assert shot_extracted['period'] == 1

        # Verify pass extraction
        assert result['first_pass'] is not None
        pass_extracted = result['first_pass']['extracted']
        assert pass_extracted['player_name'] == "Jonathan Rodríguez Menéndez"
        assert pass_extracted['statsbomb_player_id'] == 6581
        assert pass_extracted['event_type_name'] == "Pass"

        # Verify dribble extraction
        assert result['first_dribble'] is not None
        dribble_extracted = result['first_dribble']['extracted']
        assert dribble_extracted['player_name'] == "Ángel Fabián Di María Hernández"
        assert dribble_extracted['statsbomb_player_id'] == 2995
        assert dribble_extracted['event_type_name'] == "Dribble"

    def test_handles_events_without_player(self):
        """Test that function handles events without 'player' field (sets fields to None)."""
        # Given: Event without player field (like Half Start)
        event_without_player = {
            "id": str(uuid4()),
            "index": 1,
            "minute": 0,
            "second": 0,
            "type": {"id": 30, "name": "Pass"},  # Pass event but no player
            "team": {"id": 217, "name": "Barcelona"},
            "period": 1
            # No "player" field
            # No "position" field
        }

        events = [event_without_player]

        # When: Parse events
        result = parse_events_for_storage(events)

        # Then: Player fields should be None
        assert result['first_pass'] is not None
        extracted = result['first_pass']['extracted']
        assert extracted['player_name'] is None
        assert extracted['statsbomb_player_id'] is None
        assert extracted['position_name'] is None
        # But team fields should be present
        assert extracted['team_name'] == "Barcelona"
        assert extracted['statsbomb_team_id'] == 217

    def test_handles_events_without_position(self):
        """Test that function handles events without 'position' field."""
        # Given: Event with player but no position
        event_without_position = {
            "id": str(uuid4()),
            "index": 100,
            "minute": 2,
            "second": 29,
            "type": {"id": 16, "name": "Shot"},
            "team": {"id": 217, "name": "Barcelona"},
            "player": {"id": 5503, "name": "Lionel Messi"},
            "period": 1,
            "shot": {"outcome": {"id": 100, "name": "Saved"}}
            # No "position" field
        }

        events = [event_without_position]

        # When: Parse events
        result = parse_events_for_storage(events)

        # Then: Position should be None, but player fields present
        assert result['first_shot'] is not None
        extracted = result['first_shot']['extracted']
        assert extracted['player_name'] == "Lionel Messi"
        assert extracted['statsbomb_player_id'] == 5503
        assert extracted['position_name'] is None  # Missing position

    def test_returns_none_for_missing_event_types(self):
        """Test that function returns None for event types not found in data."""
        # Given: Events with only Passes (no Shots or Dribbles)
        events = [
            create_pass_event(minute=0),
            create_pass_event(minute=5),
            create_pass_event(minute=10)
        ]

        # When: Parse events
        result = parse_events_for_storage(events)

        # Then: Only first_pass should exist, others None
        assert result['first_pass'] is not None
        assert result['first_shot'] is None
        assert result['first_dribble'] is None
        assert result['filtered_count'] == 3

    def test_counts_filtered_events_correctly(self):
        """Test that function accurately counts total and filtered events."""
        # Given: 10 total events, 6 match filter (Pass/Shot/Dribble)
        events = [
            create_pass_event(),
            create_pass_event(),
            create_shot_event(),
            create_shot_event(),
            create_dribble_event(),
            create_dribble_event(),
            create_other_event(18, "Half Start"),
            create_other_event(35, "Starting XI"),
            create_other_event(19, "Substitution"),
            create_other_event(20, "Foul Committed")
        ]

        # When: Parse events
        result = parse_events_for_storage(events)

        # Then: Counts should be accurate
        assert result['total_events'] == 10
        assert result['filtered_count'] == 6


class TestInsertEvents:
    """Test insert_events main function."""

    def test_inserts_correct_count_of_events(self, session):
        """Test that function inserts only Pass, Shot, and Dribble events."""
        # Given: Match and clubs exist
        club = Club(coach_id="coach-id", club_name="Test FC", statsbomb_team_id=217)
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(opponent_name="Opponent FC", statsbomb_team_id=206)
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent_club.opponent_club_id,
            opponent_name="Opponent FC",
            match_date=date(2023, 1, 1),
            our_score=2,
            opponent_score=1,
            result='W'
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        # Given: Mix of event types (5 should be stored, 4 ignored)
        events = [
            create_pass_event(),
            create_pass_event(minute=5),
            create_shot_event(),
            create_shot_event(minute=10),
            create_dribble_event(),
            create_other_event(18, "Half Start"),
            create_other_event(35, "Starting XI"),
            create_other_event(19, "Substitution"),
            create_other_event(20, "Foul Committed")
        ]

        # When: Insert events
        count = insert_events(
            db=session,
            match_id=match.match_id,
            events=events
        )

        # Then: Only 5 events inserted (2 pass + 2 shot + 1 dribble)
        assert count == 5

        # Verify in database
        db_events = session.query(Event).filter(Event.match_id == match.match_id).all()
        assert len(db_events) == 5

    def test_batch_insert_with_large_dataset(self, session):
        """Test batch insert works correctly with >500 events."""
        # Given: Match exists
        club = Club(coach_id="coach-id", club_name="Test FC", statsbomb_team_id=217)
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(opponent_name="Opponent FC", statsbomb_team_id=206)
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent_club.opponent_club_id,
            opponent_name="Opponent FC",
            match_date=date(2023, 1, 1),
            our_score=2,
            opponent_score=1,
            result='W'
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        # Given: 600 pass events (tests batching at 500)
        events = [create_pass_event(minute=i) for i in range(600)]

        # When: Insert events
        count = insert_events(
            db=session,
            match_id=match.match_id,
            events=events
        )

        # Then: All 600 events inserted
        assert count == 600

        # Verify in database
        db_events = session.query(Event).filter(Event.match_id == match.match_id).all()
        assert len(db_events) == 600

    def test_event_data_stored_as_json(self, session):
        """Test that full event JSON is preserved in event_data field."""
        # Given: Match exists
        club = Club(coach_id="coach-id", club_name="Test FC", statsbomb_team_id=217)
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(opponent_name="Opponent FC", statsbomb_team_id=206)
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent_club.opponent_club_id,
            opponent_name="Opponent FC",
            match_date=date(2023, 1, 1),
            our_score=2,
            opponent_score=1,
            result='W'
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        # Given: Shot event with full data including freeze_frame
        shot_event = create_shot_event()
        shot_event['shot']['freeze_frame'] = [
            {"location": [101.0, 48.0], "player": {"id": 6704, "name": "Test Player"}}
        ]

        events = [shot_event]

        # When: Insert events
        insert_events(
            db=session,
            match_id=match.match_id,
            events=events
        )

        # Then: Verify full JSON preserved in event_data
        db_event = session.query(Event).filter(Event.match_id == match.match_id).first()
        assert db_event.event_data is not None
        assert db_event.event_data['shot']['freeze_frame'] is not None
        assert len(db_event.event_data['shot']['freeze_frame']) == 1

    def test_all_extracted_fields_match_database(self, session):
        """Test that all extracted fields are correctly stored in database."""
        # Given: Match exists
        club = Club(coach_id="coach-id", club_name="Test FC", statsbomb_team_id=217)
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(opponent_name="Opponent FC", statsbomb_team_id=206)
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent_club.opponent_club_id,
            opponent_name="Opponent FC",
            match_date=date(2023, 1, 1),
            our_score=2,
            opponent_score=1,
            result='W'
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        # Given: Shot event with specific data
        events = [
            create_shot_event(
                player_id=5503,
                player_name="Lionel Andrés Messi Cuccittini",
                team_id=217,
                team_name="Barcelona",
                minute=2,
                second=29,
                period=1,
                position_name="Left Center Forward"
            )
        ]

        # When: Insert events
        insert_events(
            db=session,
            match_id=match.match_id,
            events=events
        )

        # Then: Verify all fields match
        db_event = session.query(Event).filter(Event.match_id == match.match_id).first()
        assert db_event.player_name == "Lionel Andrés Messi Cuccittini"
        assert db_event.statsbomb_player_id == 5503
        assert db_event.team_name == "Barcelona"
        assert db_event.statsbomb_team_id == 217
        assert db_event.event_type_name == "Shot"
        assert db_event.position_name == "Left Center Forward"
        assert db_event.minute == 2
        assert db_event.second == 29
        assert db_event.period == 1

    def test_handles_events_without_player(self, session):
        """Test that function handles events without player field (nullable fields)."""
        # Given: Match exists
        club = Club(coach_id="coach-id", club_name="Test FC", statsbomb_team_id=217)
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(opponent_name="Opponent FC", statsbomb_team_id=206)
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent_club.opponent_club_id,
            opponent_name="Opponent FC",
            match_date=date(2023, 1, 1),
            our_score=2,
            opponent_score=1,
            result='W'
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        # Given: Event without player field
        event_without_player = {
            "id": str(uuid4()),
            "index": 1,
            "minute": 0,
            "second": 0,
            "type": {"id": 30, "name": "Pass"},
            "team": {"id": 217, "name": "Barcelona"},
            "period": 1
            # No "player" or "position" field
        }

        events = [event_without_player]

        # When: Insert events
        insert_events(
            db=session,
            match_id=match.match_id,
            events=events
        )

        # Then: Event inserted with nullable fields as None
        db_event = session.query(Event).filter(Event.match_id == match.match_id).first()
        assert db_event.player_name is None
        assert db_event.statsbomb_player_id is None
        assert db_event.position_name is None
        # But team fields should be present
        assert db_event.team_name == "Barcelona"
        assert db_event.statsbomb_team_id == 217

    def test_raises_error_if_match_not_found(self, session):
        """Test that function raises ValueError if match_id doesn't exist."""
        # Given: No match exists
        fake_match_id = uuid4()
        events = [create_pass_event()]

        # When/Then: Should raise ValueError
        with pytest.raises(ValueError, match="Match with ID .* not found"):
            insert_events(
                db=session,
                match_id=fake_match_id,
                events=events
            )

    def test_raises_error_if_zero_filtered_events(self, session):
        """Test that function raises ValueError if no Pass/Shot/Dribble events found."""
        # Given: Match exists
        club = Club(coach_id="coach-id", club_name="Test FC", statsbomb_team_id=217)
        session.add(club)
        session.commit()
        session.refresh(club)

        opponent_club = OpponentClub(opponent_name="Opponent FC", statsbomb_team_id=206)
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        match = Match(
            club_id=club.club_id,
            opponent_club_id=opponent_club.opponent_club_id,
            opponent_name="Opponent FC",
            match_date=date(2023, 1, 1),
            our_score=2,
            opponent_score=1,
            result='W'
        )
        session.add(match)
        session.commit()
        session.refresh(match)

        # Given: Events with no Pass/Shot/Dribble (only other types)
        events = [
            create_other_event(18, "Half Start"),
            create_other_event(35, "Starting XI"),
            create_other_event(19, "Substitution")
        ]

        # When/Then: Should raise ValueError
        with pytest.raises(ValueError, match="No Pass, Shot, or Dribble events found"):
            insert_events(
                db=session,
                match_id=match.match_id,
                events=events
            )
