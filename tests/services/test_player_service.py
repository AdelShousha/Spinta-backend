"""
Tests for player service.
"""

import pytest
from uuid import UUID

from app.services.player_service import (
    parse_our_lineup_from_events,
    extract_our_players,
    parse_opponent_lineup_from_events,
    extract_opponent_players
)
from app.models.club import Club
from app.models.player import Player
from app.models.opponent_club import OpponentClub
from app.models.opponent_player import OpponentPlayer


def create_starting_xi_event(team_id: int, team_name: str, player_count: int = 11) -> dict:
    """Helper to create a Starting XI event with specified team and player count."""
    return {
        "id": f"event-{team_id}",
        "type": {"id": 35, "name": "Starting XI"},
        "team": {"id": team_id, "name": team_name},
        "tactics": {
            "formation": 433,
            "lineup": [
                {
                    "player": {"id": 5500 + i, "name": f"Player {i}"},
                    "position": {"id": i, "name": f"Position {i}"},
                    "jersey_number": i
                }
                for i in range(1, player_count + 1)
            ]
        }
    }


class TestParseOurLineupFromEvents:
    """Test parse_our_lineup_from_events helper function."""

    def test_extracts_11_players(self):
        """Test that function extracts all 11 players from our team's Starting XI."""
        events = [
            create_starting_xi_event(779, "Argentina"),
            create_starting_xi_event(792, "Australia")
        ]

        lineup = parse_our_lineup_from_events(
            events=events,
            our_club_statsbomb_team_id=779
        )

        # Should extract 11 players
        assert len(lineup) == 11

        # Verify first player structure
        assert 'player_name' in lineup[0]
        assert 'statsbomb_player_id' in lineup[0]
        assert 'jersey_number' in lineup[0]
        assert 'position' in lineup[0]

        # Verify data extracted correctly
        assert lineup[0]['player_name'] == "Player 1"
        assert lineup[0]['statsbomb_player_id'] == 5501
        assert lineup[0]['jersey_number'] == 1
        assert lineup[0]['position'] == "Position 1"

    def test_finds_correct_team_by_team_id(self):
        """Test that function identifies our team by matching team.id."""
        events = [
            create_starting_xi_event(779, "Argentina"),
            create_starting_xi_event(792, "Australia")
        ]

        # Test with team 1 (Argentina)
        lineup_argentina = parse_our_lineup_from_events(
            events=events,
            our_club_statsbomb_team_id=779
        )
        assert len(lineup_argentina) == 11
        assert lineup_argentina[0]['statsbomb_player_id'] == 5501  # Argentina's player

        # Test with team 2 (Australia)
        lineup_australia = parse_our_lineup_from_events(
            events=events,
            our_club_statsbomb_team_id=792
        )
        assert len(lineup_australia) == 11
        assert lineup_australia[0]['statsbomb_player_id'] == 5501  # Australia's player

    def test_validation_error_not_11_players(self):
        """Test error when lineup doesn't have exactly 11 players."""
        # Create event with only 10 players
        events = [
            create_starting_xi_event(779, "Argentina", player_count=10),
            create_starting_xi_event(792, "Australia")
        ]

        with pytest.raises(ValueError, match="has 10 players.*expected 11"):
            parse_our_lineup_from_events(
                events=events,
                our_club_statsbomb_team_id=779
            )

    def test_validation_error_no_starting_xi(self):
        """Test error when no Starting XI events found."""
        # Events without Starting XI
        events = [
            {
                "id": "pass-1",
                "type": {"id": 30, "name": "Pass"},
                "team": {"id": 779, "name": "Argentina"}
            }
        ]

        with pytest.raises(ValueError, match="Expected 2 Starting XI events"):
            parse_our_lineup_from_events(
                events=events,
                our_club_statsbomb_team_id=779
            )

    def test_validation_error_team_not_found(self):
        """Test error when our team ID doesn't match either Starting XI event."""
        events = [
            create_starting_xi_event(779, "Argentina"),
            create_starting_xi_event(792, "Australia")
        ]

        with pytest.raises(ValueError, match="Team with StatsBomb ID 999 not found"):
            parse_our_lineup_from_events(
                events=events,
                our_club_statsbomb_team_id=999  # Wrong ID
            )


class TestExtractOurPlayers:
    """Test extract_our_players function."""

    def test_creates_11_incomplete_players(self, session):
        """Test that function creates 11 incomplete Player records."""
        # Given: Club exists
        club = Club(
            coach_id="coach-id-placeholder",
            club_name="Test FC",
            statsbomb_team_id=779
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        # Given: Events with Starting XI
        events = [
            create_starting_xi_event(779, "Test FC"),
            create_starting_xi_event(792, "Opponent FC")
        ]

        # When: Extract players
        result = extract_our_players(
            db=session,
            club_id=club.club_id,
            events=events
        )

        # Then: 11 players created (none updated since all new)
        assert result['players_processed'] == 11
        assert result['players_created'] == 11
        assert result['players_updated'] == 0
        assert len(result['players']) == 11

        # Verify players in database
        players = session.query(Player).filter(Player.club_id == club.club_id).all()
        assert len(players) == 11

    def test_generates_unique_invite_codes(self, session):
        """Test that all invite codes are unique and follow format XXX-####."""
        # Given: Club exists
        club = Club(
            coach_id="coach-id-placeholder",
            club_name="Test FC",
            statsbomb_team_id=779
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        # Given: Events with Starting XI
        events = [
            create_starting_xi_event(779, "Test FC"),
            create_starting_xi_event(792, "Opponent FC")
        ]

        # When: Extract players
        result = extract_our_players(
            db=session,
            club_id=club.club_id,
            events=events
        )

        # Then: All invite codes are unique
        invite_codes = [p['invite_code'] for p in result['players']]
        assert len(invite_codes) == len(set(invite_codes))  # No duplicates

        # Verify format: XXX-#### (3 uppercase letters, dash, 4 digits)
        import re
        pattern = r'^[A-Z]{3}-\d{4}$'
        for code in invite_codes:
            assert re.match(pattern, code), f"Invite code {code} doesn't match format XXX-####"

    def test_sets_all_fields_correctly(self, session):
        """Test that all player fields are set correctly from lineup data."""
        # Given: Club exists
        club = Club(
            coach_id="coach-id-placeholder",
            club_name="Test FC",
            statsbomb_team_id=779
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        # Given: Events with Starting XI
        events = [
            create_starting_xi_event(779, "Test FC"),
            create_starting_xi_event(792, "Opponent FC")
        ]

        # When: Extract players
        result = extract_our_players(
            db=session,
            club_id=club.club_id,
            events=events
        )

        # Then: Verify first player's fields
        first_player = result['players'][0]
        assert isinstance(first_player['player_id'], (UUID, str))
        assert first_player['player_name'] == "Player 1"
        assert first_player['statsbomb_player_id'] == 5501
        assert first_player['jersey_number'] == 1
        assert first_player['position'] == "Position 1"
        assert 'invite_code' in first_player

        # Verify in database
        db_player = session.query(Player).filter(
            Player.player_id == first_player['player_id']
        ).first()
        assert db_player is not None
        assert db_player.club_id == club.club_id
        assert db_player.player_name == "Player 1"
        assert db_player.statsbomb_player_id == 5501
        assert db_player.jersey_number == 1
        assert db_player.position == "Position 1"

    def test_sets_is_linked_false(self, session):
        """Test that all players are created with is_linked=False (incomplete players)."""
        # Given: Club exists
        club = Club(
            coach_id="coach-id-placeholder",
            club_name="Test FC",
            statsbomb_team_id=779
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        # Given: Events with Starting XI
        events = [
            create_starting_xi_event(779, "Test FC"),
            create_starting_xi_event(792, "Opponent FC")
        ]

        # When: Extract players
        result = extract_our_players(
            db=session,
            club_id=club.club_id,
            events=events
        )

        # Then: All players have is_linked=False
        players = session.query(Player).filter(Player.club_id == club.club_id).all()
        for player in players:
            assert player.is_linked is False
            assert player.user_id is None  # user_id should be NULL
            assert player.linked_at is None  # linked_at should be NULL

    def test_updates_existing_incomplete_player(self, session):
        """Test updating existing incomplete player when jersey/position changed."""
        # Given: Club exists
        club = Club(
            coach_id="coach-id-placeholder",
            club_name="Test FC",
            statsbomb_team_id=779
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        # Given: Existing incomplete player with old jersey/position
        existing_player = Player(
            club_id=club.club_id,
            player_name="Player 1",
            statsbomb_player_id=5501,
            jersey_number=99,  # Old jersey
            position="Old Position",  # Old position
            invite_code="ABC-1234",
            is_linked=False,
            user_id=None
        )
        session.add(existing_player)
        session.commit()
        session.refresh(existing_player)
        existing_id = existing_player.player_id

        # Given: Events with updated jersey/position
        events = [
            create_starting_xi_event(779, "Test FC"),
            create_starting_xi_event(792, "Opponent FC")
        ]

        # When: Extract players
        result = extract_our_players(
            db=session,
            club_id=club.club_id,
            events=events
        )

        # Then: 10 created, 1 updated
        assert result['players_processed'] == 11
        assert result['players_created'] == 10
        assert result['players_updated'] == 1

        # Verify existing player was updated
        session.refresh(existing_player)
        assert existing_player.player_id == existing_id  # Same ID
        assert existing_player.jersey_number == 1  # Updated
        assert existing_player.position == "Position 1"  # Updated
        assert existing_player.player_name == "Player 1"  # Preserved (not "Player 1" from events)

    def test_preserves_invite_code_on_update(self, session):
        """Test that invite code is preserved when updating existing player."""
        # Given: Club exists
        club = Club(
            coach_id="coach-id-placeholder",
            club_name="Test FC",
            statsbomb_team_id=779
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        # Given: Existing incomplete player with specific invite code
        original_invite_code = "XYZ-9999"
        existing_player = Player(
            club_id=club.club_id,
            player_name="Player 1",
            statsbomb_player_id=5501,
            jersey_number=99,
            position="Old Position",
            invite_code=original_invite_code,
            is_linked=False,
            user_id=None
        )
        session.add(existing_player)
        session.commit()

        # Given: Events
        events = [
            create_starting_xi_event(779, "Test FC"),
            create_starting_xi_event(792, "Opponent FC")
        ]

        # When: Extract players
        result = extract_our_players(
            db=session,
            club_id=club.club_id,
            events=events
        )

        # Then: Invite code preserved
        session.refresh(existing_player)
        assert existing_player.invite_code == original_invite_code  # NOT regenerated!

        # Verify in result
        updated_player = [p for p in result['players'] if p['player_id'] == existing_player.player_id][0]
        assert updated_player['invite_code'] == original_invite_code

    def test_skips_linked_players(self, session):
        """Test that linked players are skipped (not updated) and counted as processed."""
        # Given: Club exists
        club = Club(
            coach_id="coach-id-placeholder",
            club_name="Test FC",
            statsbomb_team_id=779
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        # Given: Existing LINKED player (is_linked=True, has user_id)
        from uuid import uuid4
        linked_player = Player(
            club_id=club.club_id,
            player_name="Player 1",
            statsbomb_player_id=5501,
            jersey_number=99,  # Old jersey
            position="Old Position",  # Old position
            invite_code="ABC-1234",
            is_linked=True,  # LINKED!
            user_id=uuid4()  # Has user account
        )
        session.add(linked_player)
        session.commit()
        session.refresh(linked_player)

        # Given: Events with different jersey/position
        events = [
            create_starting_xi_event(779, "Test FC"),
            create_starting_xi_event(792, "Opponent FC")
        ]

        # When: Extract players
        result = extract_our_players(
            db=session,
            club_id=club.club_id,
            events=events
        )

        # Then: 10 created, 0 updated (linked player skipped), 1 already linked
        assert result['players_processed'] == 11
        assert result['players_created'] == 10
        assert result['players_updated'] == 0

        # Verify linked player was NOT updated
        session.refresh(linked_player)
        assert linked_player.jersey_number == 99  # NOT updated
        assert linked_player.position == "Old Position"  # NOT updated
        assert linked_player.is_linked is True  # Still linked

    def test_no_update_if_same_data(self, session):
        """Test that player is not updated if jersey/position unchanged."""
        # Given: Club exists
        club = Club(
            coach_id="coach-id-placeholder",
            club_name="Test FC",
            statsbomb_team_id=779
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        # Given: Existing player with same data as events
        existing_player = Player(
            club_id=club.club_id,
            player_name="Player 1",
            statsbomb_player_id=5501,
            jersey_number=1,  # Same as in event
            position="Position 1",  # Same as in event
            invite_code="ABC-1234",
            is_linked=False,
            user_id=None
        )
        session.add(existing_player)
        session.commit()

        # Given: Events
        events = [
            create_starting_xi_event(779, "Test FC"),
            create_starting_xi_event(792, "Opponent FC")
        ]

        # When: Extract players
        result = extract_our_players(
            db=session,
            club_id=club.club_id,
            events=events
        )

        # Then: 10 created, 1 "processed" but not actually updated
        assert result['players_processed'] == 11
        assert result['players_created'] == 10
        # Updated count is 0 because no changes made
        assert result['players_updated'] == 0

    def test_mixed_create_and_update(self, session):
        """Test mix of creating new and updating existing players."""
        # Given: Club exists
        club = Club(
            coach_id="coach-id-placeholder",
            club_name="Test FC",
            statsbomb_team_id=779
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        # Given: 3 existing incomplete players
        for i in [1, 2, 3]:
            player = Player(
                club_id=club.club_id,
                player_name=f"Player {i}",
                statsbomb_player_id=5500 + i,
                jersey_number=99,  # Will be updated
                position="Old Position",
                invite_code=f"OLD-{i:04d}",
                is_linked=False,
                user_id=None
            )
            session.add(player)
        session.commit()

        # Given: Events with 11 players
        events = [
            create_starting_xi_event(779, "Test FC"),
            create_starting_xi_event(792, "Opponent FC")
        ]

        # When: Extract players
        result = extract_our_players(
            db=session,
            club_id=club.club_id,
            events=events
        )

        # Then: 8 created, 3 updated
        assert result['players_processed'] == 11
        assert result['players_created'] == 8
        assert result['players_updated'] == 3


class TestParseOpponentLineupFromEvents:
    """Test parse_opponent_lineup_from_events helper function."""

    def test_extracts_11_opponent_players(self):
        """Test that function extracts all 11 players from opponent's Starting XI."""
        events = [
            create_starting_xi_event(779, "Argentina"),
            create_starting_xi_event(792, "Australia")
        ]

        lineup = parse_opponent_lineup_from_events(
            events=events,
            opponent_statsbomb_team_id=792
        )

        # Should extract 11 players
        assert len(lineup) == 11

        # Verify structure
        assert 'player_name' in lineup[0]
        assert 'statsbomb_player_id' in lineup[0]
        assert 'jersey_number' in lineup[0]
        assert 'position' in lineup[0]

    def test_finds_correct_opponent_team(self):
        """Test that function identifies opponent team by team.id."""
        events = [
            create_starting_xi_event(779, "Argentina"),
            create_starting_xi_event(792, "Australia")
        ]

        # Get Australia's lineup
        lineup = parse_opponent_lineup_from_events(
            events=events,
            opponent_statsbomb_team_id=792
        )
        assert len(lineup) == 11


class TestExtractOpponentPlayers:
    """Test extract_opponent_players function."""

    def test_creates_new_opponent_players(self, session):
        """Test creating 11 new opponent player records."""
        # Given: Opponent club exists
        opponent_club = OpponentClub(
            statsbomb_team_id=792,
            opponent_name="Australia"
        )
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        # Given: Events with Starting XI
        events = [
            create_starting_xi_event(779, "Argentina"),
            create_starting_xi_event(792, "Australia")
        ]

        # When: Extract opponent players
        result = extract_opponent_players(
            db=session,
            opponent_club_id=opponent_club.opponent_club_id,
            events=events
        )

        # Then: 11 players created
        assert result['players_processed'] == 11
        assert result['players_created'] == 11
        assert result['players_updated'] == 0
        assert len(result['players']) == 11

        # Verify in database
        players = session.query(OpponentPlayer).filter(
            OpponentPlayer.opponent_club_id == opponent_club.opponent_club_id
        ).all()
        assert len(players) == 11

    def test_updates_existing_by_statsbomb_id(self, session):
        """Test updating existing opponent players if jersey/position changed."""
        # Given: Opponent club exists
        opponent_club = OpponentClub(
            statsbomb_team_id=792,
            opponent_name="Australia"
        )
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        # Given: Existing opponent player with old jersey/position
        existing_player = OpponentPlayer(
            opponent_club_id=opponent_club.opponent_club_id,
            player_name="Player 1",
            statsbomb_player_id=5501,
            jersey_number=99,  # Old jersey
            position="Old Position"  # Old position
        )
        session.add(existing_player)
        session.commit()
        session.refresh(existing_player)
        existing_id = existing_player.opponent_player_id

        # Given: Events with updated jersey/position
        events = [
            create_starting_xi_event(779, "Argentina"),
            create_starting_xi_event(792, "Australia")
        ]

        # When: Extract opponent players
        result = extract_opponent_players(
            db=session,
            opponent_club_id=opponent_club.opponent_club_id,
            events=events
        )

        # Then: 10 created, 1 updated
        assert result['players_processed'] == 11
        assert result['players_created'] == 10
        assert result['players_updated'] == 1

        # Verify existing player was updated
        session.refresh(existing_player)
        assert existing_player.opponent_player_id == existing_id  # Same ID
        assert existing_player.jersey_number == 1  # Updated
        assert existing_player.position == "Position 1"  # Updated

    def test_no_update_if_same_data(self, session):
        """Test that player is not updated if jersey/position unchanged."""
        # Given: Opponent club exists
        opponent_club = OpponentClub(
            statsbomb_team_id=792,
            opponent_name="Australia"
        )
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        # Given: Existing player with same data
        existing_player = OpponentPlayer(
            opponent_club_id=opponent_club.opponent_club_id,
            player_name="Player 1",
            statsbomb_player_id=5501,
            jersey_number=1,  # Same as in event
            position="Position 1"  # Same as in event
        )
        session.add(existing_player)
        session.commit()

        # Given: Events
        events = [
            create_starting_xi_event(779, "Argentina"),
            create_starting_xi_event(792, "Australia")
        ]

        # When: Extract opponent players
        result = extract_opponent_players(
            db=session,
            opponent_club_id=opponent_club.opponent_club_id,
            events=events
        )

        # Then: 10 created, 1 "processed" but not actually updated
        assert result['players_processed'] == 11
        assert result['players_created'] == 10
        # Updated count is 0 because no changes made
        assert result['players_updated'] == 0

    def test_mixed_create_and_update(self, session):
        """Test mix of creating new and updating existing players."""
        # Given: Opponent club exists
        opponent_club = OpponentClub(
            statsbomb_team_id=792,
            opponent_name="Australia"
        )
        session.add(opponent_club)
        session.commit()
        session.refresh(opponent_club)

        # Given: 3 existing players
        for i in [1, 2, 3]:
            player = OpponentPlayer(
                opponent_club_id=opponent_club.opponent_club_id,
                player_name=f"Player {i}",
                statsbomb_player_id=5500 + i,
                jersey_number=99,  # Will be updated
                position="Old Position"
            )
            session.add(player)
        session.commit()

        # Given: Events with 11 players
        events = [
            create_starting_xi_event(779, "Argentina"),
            create_starting_xi_event(792, "Australia")
        ]

        # When: Extract opponent players
        result = extract_opponent_players(
            db=session,
            opponent_club_id=opponent_club.opponent_club_id,
            events=events
        )

        # Then: 8 created, 3 updated
        assert result['players_processed'] == 11
        assert result['players_created'] == 8
        assert result['players_updated'] == 3
