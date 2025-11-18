"""
Tests for team identification and opponent club handling service.
"""

import pytest
from uuid import UUID
from app.services.team_identifier import (
    fuzzy_match_team_name,
    get_or_create_opponent_club,
    identify_teams_and_opponent
)


# Sample Starting XI events for testing
def create_starting_xi_event(team_id: int, team_name: str, player_count: int = 11):
    """Helper to create a Starting XI event with specified team and player count."""
    return {
        "id": f"event-{team_id}",
        "index": 1,
        "period": 1,
        "timestamp": "00:00:00.000",
        "minute": 0,
        "second": 0,
        "type": {"id": 35, "name": "Starting XI"},
        "possession": 1,
        "possession_team": {"id": team_id, "name": team_name},
        "team": {"id": team_id, "name": team_name},
        "duration": 0.0,
        "tactics": {
            "formation": 433,
            "lineup": [
                {
                    "player": {"id": i, "name": f"Player {i}"},
                    "position": {"id": i, "name": f"Position {i}"},
                    "jersey_number": i
                }
                for i in range(1, player_count + 1)
            ]
        }
    }


def create_sample_events(team_1_id=779, team_1_name="Argentina",
                         team_2_id=792, team_2_name="Australia"):
    """Helper to create sample events with 2 Starting XI events."""
    return [
        create_starting_xi_event(team_1_id, team_1_name),
        create_starting_xi_event(team_2_id, team_2_name),
        # Add some other events to simulate real data
        {
            "id": "event-3",
            "type": {"id": 30, "name": "Pass"},
            "team": {"id": team_1_id, "name": team_1_name}
        }
    ]


class TestFuzzyMatching:
    """Test fuzzy name matching logic."""

    def test_exact_match_team_1(self):
        """Test exact match with first team."""
        result = fuzzy_match_team_name("Argentina", "Argentina", "Australia")
        assert result == 1

    def test_exact_match_team_2(self):
        """Test exact match with second team."""
        result = fuzzy_match_team_name("Australia", "Argentina", "Australia")
        assert result == 2

    def test_exact_match_case_insensitive(self):
        """Test exact match is case-insensitive."""
        result = fuzzy_match_team_name("argentina", "ARGENTINA", "Australia")
        assert result == 1

    def test_substring_match_team_1(self):
        """Test substring match (e.g., 'Thunder United FC' vs 'Thunder United')."""
        result = fuzzy_match_team_name("Thunder United", "Thunder United FC", "City Strikers")
        assert result == 1

    def test_substring_match_reverse(self):
        """Test substring match in reverse (DB has 'FC', event doesn't)."""
        result = fuzzy_match_team_name("Thunder United FC", "Thunder United", "City Strikers")
        assert result == 1

    def test_fuzzy_match_80_percent(self):
        """Test fuzzy match at 80% threshold."""
        result = fuzzy_match_team_name("Juventus FC", "Juventus", "Real Madrid")
        assert result == 1

    def test_no_match_below_threshold(self):
        """Test no match when similarity < 80%."""
        result = fuzzy_match_team_name("Barcelona", "Real Madrid", "Manchester United")
        assert result is None


class TestTeamIdentification:
    """Test team identification logic for first and subsequent matches."""

    def test_first_match_exact_name(self):
        """Test first match with exact name match."""
        events = create_sample_events()
        result = identify_teams_and_opponent(
            club_name="Argentina",
            club_statsbomb_team_id=None,
            events=events,
            opponent_name="Australia",
            opponent_logo_url="https://example.com/australia.png"
        )

        assert result['our_team_id'] == 779
        assert result['our_team_name'] == "Argentina"
        assert result['opponent_team_id'] == 792
        assert result['opponent_team_name'] == "Australia"
        assert result['should_update_club_statsbomb_id'] is True
        assert result['new_statsbomb_team_id'] == 779

    def test_first_match_substring(self):
        """Test first match with substring match."""
        events = create_sample_events(team_1_name="Argentina FC")
        result = identify_teams_and_opponent(
            club_name="Argentina",
            club_statsbomb_team_id=None,
            events=events,
            opponent_name="Australia",
            opponent_logo_url="https://example.com/australia.png"
        )

        assert result['our_team_id'] == 779
        assert result['our_team_name'] == "Argentina FC"
        assert result['should_update_club_statsbomb_id'] is True

    def test_first_match_fuzzy_80_percent(self):
        """Test first match with fuzzy match at 80% threshold."""
        # "Thunder United" vs "Thunder Utd" has ~85% similarity
        events = create_sample_events(
            team_1_id=779,
            team_1_name="Thunder Utd",
            team_2_id=792,
            team_2_name="Australia"
        )
        result = identify_teams_and_opponent(
            club_name="Thunder United",
            club_statsbomb_team_id=None,
            events=events,
            opponent_name="Australia",
            opponent_logo_url="https://example.com/australia.png"
        )

        assert result['our_team_id'] == 779
        assert result['our_team_name'] == "Thunder Utd"
        assert result['should_update_club_statsbomb_id'] is True

    def test_first_match_team_2_is_ours(self):
        """Test first match when our team is the second Starting XI event."""
        events = create_sample_events()
        result = identify_teams_and_opponent(
            club_name="Australia",
            club_statsbomb_team_id=None,
            events=events,
            opponent_name="Argentina",
            opponent_logo_url="https://example.com/argentina.png"
        )

        assert result['our_team_id'] == 792
        assert result['our_team_name'] == "Australia"
        assert result['opponent_team_id'] == 779
        assert result['opponent_team_name'] == "Argentina"

    def test_first_match_no_match_error(self):
        """Test error when club name doesn't match either team."""
        events = create_sample_events()
        with pytest.raises(ValueError, match="Cannot match your club name"):
            identify_teams_and_opponent(
                club_name="Brazil",
                club_statsbomb_team_id=None,
                events=events,
                opponent_name="Australia",
                opponent_logo_url="https://example.com/australia.png"
            )

    def test_subsequent_match_direct_id_match_team_1(self):
        """Test subsequent match with direct StatsBomb team ID match (team 1)."""
        events = create_sample_events()
        result = identify_teams_and_opponent(
            club_name="Argentina",
            club_statsbomb_team_id=779,  # Already set from first match
            events=events,
            opponent_name="Australia",
            opponent_logo_url="https://example.com/australia.png"
        )

        assert result['our_team_id'] == 779
        assert result['our_team_name'] == "Argentina"
        assert result['opponent_team_id'] == 792
        assert result['should_update_club_statsbomb_id'] is False
        assert result['new_statsbomb_team_id'] is None

    def test_subsequent_match_direct_id_match_team_2(self):
        """Test subsequent match with direct StatsBomb team ID match (team 2)."""
        events = create_sample_events()
        result = identify_teams_and_opponent(
            club_name="Australia",
            club_statsbomb_team_id=792,
            events=events,
            opponent_name="Argentina",
            opponent_logo_url="https://example.com/argentina.png"
        )

        assert result['our_team_id'] == 792
        assert result['our_team_name'] == "Australia"
        assert result['opponent_team_id'] == 779
        assert result['should_update_club_statsbomb_id'] is False

    def test_subsequent_match_id_not_found_error(self):
        """Test error when club's statsbomb_team_id doesn't match either team."""
        events = create_sample_events()
        with pytest.raises(ValueError, match="doesn't match either team"):
            identify_teams_and_opponent(
                club_name="Argentina",
                club_statsbomb_team_id=999,  # Wrong ID
                events=events,
                opponent_name="Australia",
                opponent_logo_url="https://example.com/australia.png"
            )


class TestValidationErrors:
    """Test validation error handling."""

    def test_error_not_two_starting_xi(self):
        """Test error when events don't have exactly 2 Starting XI events."""
        # Only 1 Starting XI event
        events = [create_starting_xi_event(779, "Argentina")]

        with pytest.raises(ValueError, match="Expected 2 Starting XI events, found 1"):
            identify_teams_and_opponent(
                club_name="Argentina",
                club_statsbomb_team_id=None,
                events=events,
                opponent_name="Australia",
                opponent_logo_url="https://example.com/australia.png"
            )

    def test_error_three_starting_xi(self):
        """Test error when events have 3 Starting XI events."""
        events = [
            create_starting_xi_event(779, "Argentina"),
            create_starting_xi_event(792, "Australia"),
            create_starting_xi_event(800, "Brazil")
        ]

        with pytest.raises(ValueError, match="Expected 2 Starting XI events, found 3"):
            identify_teams_and_opponent(
                club_name="Argentina",
                club_statsbomb_team_id=None,
                events=events,
                opponent_name="Australia",
                opponent_logo_url="https://example.com/australia.png"
            )

    def test_error_lineup_not_11_players(self):
        """Test error when lineup doesn't have 11 players."""
        events = [
            create_starting_xi_event(779, "Argentina", player_count=10),  # Only 10 players
            create_starting_xi_event(792, "Australia", player_count=11)
        ]

        with pytest.raises(ValueError, match="has 10 players \\(expected 11\\)"):
            identify_teams_and_opponent(
                club_name="Argentina",
                club_statsbomb_team_id=None,
                events=events,
                opponent_name="Australia",
                opponent_logo_url="https://example.com/australia.png"
            )

    def test_error_both_lineups_wrong(self):
        """Test error when both lineups have wrong player count."""
        events = [
            create_starting_xi_event(779, "Argentina", player_count=12),
            create_starting_xi_event(792, "Australia", player_count=10)
        ]

        with pytest.raises(ValueError, match="expected 11"):
            identify_teams_and_opponent(
                club_name="Argentina",
                club_statsbomb_team_id=None,
                events=events,
                opponent_name="Australia",
                opponent_logo_url="https://example.com/australia.png"
            )


class TestOpponentClubHandling:
    """Test opponent club get/create logic."""

    def test_get_existing_opponent_by_id(self):
        """Test retrieving existing opponent club by StatsBomb team ID."""
        existing_uuid = UUID('12345678-1234-5678-1234-567812345678')
        existing_opponents = [
            {
                'opponent_club_id': existing_uuid,
                'statsbomb_team_id': 792,
                'opponent_name': 'Australia',
                'logo_url': 'https://old-url.com/logo.png'
            }
        ]

        result = get_or_create_opponent_club(
            statsbomb_team_id=792,
            opponent_name="Australia Updated",
            opponent_logo_url="https://new-url.com/logo.png",
            existing_opponents=existing_opponents
        )

        assert result['opponent_club_id'] == existing_uuid
        assert result['statsbomb_team_id'] == 792
        assert result['is_new'] is False
        # Should return existing data, not new data from request
        assert result['opponent_name'] == 'Australia'
        assert result['logo_url'] == 'https://old-url.com/logo.png'

    def test_create_new_opponent(self):
        """Test creating new opponent club when not found."""
        result = get_or_create_opponent_club(
            statsbomb_team_id=792,
            opponent_name="Australia",
            opponent_logo_url="https://example.com/australia.png",
            existing_opponents=[]
        )

        assert isinstance(result['opponent_club_id'], UUID)
        assert result['statsbomb_team_id'] == 792
        assert result['is_new'] is True
        # Should use data from request body
        assert result['opponent_name'] == "Australia"
        assert result['logo_url'] == "https://example.com/australia.png"

    def test_uses_request_body_data_for_new_opponent(self):
        """Test that opponent_name and logo_url from request body are used when creating."""
        result = get_or_create_opponent_club(
            statsbomb_team_id=800,
            opponent_name="Brazil National Team",
            opponent_logo_url="https://example.com/brazil-logo.png",
            existing_opponents=None
        )

        assert result['opponent_name'] == "Brazil National Team"
        assert result['logo_url'] == "https://example.com/brazil-logo.png"
        assert result['is_new'] is True

    def test_match_only_by_id_not_name(self):
        """Test that matching uses ONLY statsbomb_team_id, not opponent_name."""
        existing_uuid = UUID('12345678-1234-5678-1234-567812345678')
        existing_opponents = [
            {
                'opponent_club_id': existing_uuid,
                'statsbomb_team_id': 792,
                'opponent_name': 'Australia Old Name',
                'logo_url': 'https://old.com/logo.png'
            }
        ]

        # Same ID, different name - should still match
        result = get_or_create_opponent_club(
            statsbomb_team_id=792,
            opponent_name="Completely Different Name",
            opponent_logo_url="https://new.com/logo.png",
            existing_opponents=existing_opponents
        )

        assert result['opponent_club_id'] == existing_uuid
        assert result['is_new'] is False


class TestEndToEnd:
    """End-to-end tests with real StatsBomb data structure."""

    def test_with_real_statsbomb_data(self):
        """Test with realistic StatsBomb event structure."""
        events = [
            {
                "id": "8a6b78c5-b82f-4204-88ae-69b8b3057df6",
                "index": 1,
                "period": 1,
                "timestamp": "00:00:00.000",
                "minute": 0,
                "second": 0,
                "type": {"id": 35, "name": "Starting XI"},
                "possession": 1,
                "possession_team": {"id": 779, "name": "Argentina"},
                "play_pattern": {"id": 1, "name": "Regular Play"},
                "team": {"id": 779, "name": "Argentina"},
                "duration": 0.0,
                "tactics": {
                    "formation": 433,
                    "lineup": [
                        {
                            "player": {"id": 5503, "name": "Lionel Andrés Messi Cuccittini"},
                            "position": {"id": 23, "name": "Center Forward"},
                            "jersey_number": 10
                        },
                        # ... 10 more players (simplified for test)
                        *[
                            {
                                "player": {"id": 6000 + i, "name": f"Player {i}"},
                                "position": {"id": i, "name": f"Position {i}"},
                                "jersey_number": i
                            }
                            for i in range(1, 11)
                        ]
                    ]
                }
            },
            {
                "id": "9b58cb10-893b-46aa-9d29-d3c0b6a75008",
                "index": 2,
                "period": 1,
                "timestamp": "00:00:00.000",
                "minute": 0,
                "second": 0,
                "type": {"id": 35, "name": "Starting XI"},
                "possession": 1,
                "possession_team": {"id": 779, "name": "Argentina"},
                "play_pattern": {"id": 1, "name": "Regular Play"},
                "team": {"id": 792, "name": "Australia"},
                "duration": 0.0,
                "tactics": {
                    "formation": 442,
                    "lineup": [
                        {
                            "player": {"id": 3240, "name": "Mathew Ryan"},
                            "position": {"id": 1, "name": "Goalkeeper"},
                            "jersey_number": 1
                        },
                        # ... 10 more players
                        *[
                            {
                                "player": {"id": 3000 + i, "name": f"Player {i}"},
                                "position": {"id": i, "name": f"Position {i}"},
                                "jersey_number": i
                            }
                            for i in range(2, 12)
                        ]
                    ]
                }
            },
            # Add some non-Starting XI events
            {
                "id": "event-3",
                "type": {"id": 30, "name": "Pass"},
                "team": {"id": 779, "name": "Argentina"}
            },
            {
                "id": "event-4",
                "type": {"id": 16, "name": "Shot"},
                "team": {"id": 792, "name": "Australia"}
            }
        ]

        result = identify_teams_and_opponent(
            club_name="Argentina",
            club_statsbomb_team_id=None,
            events=events,
            opponent_name="Australia",
            opponent_logo_url="https://example.com/australia.png"
        )

        assert result['our_team_id'] == 779
        assert result['our_team_name'] == "Argentina"
        assert result['opponent_team_id'] == 792
        assert result['opponent_team_name'] == "Australia"
        assert isinstance(result['opponent_club_id'], UUID)
        assert result['should_update_club_statsbomb_id'] is True
        assert result['new_statsbomb_team_id'] == 779

    def test_complete_flow_first_then_subsequent_match(self):
        """Test complete flow: first match then subsequent match."""
        events = create_sample_events()

        # First match
        first_result = identify_teams_and_opponent(
            club_name="Argentina",
            club_statsbomb_team_id=None,
            events=events,
            opponent_name="Australia",
            opponent_logo_url="https://example.com/australia.png"
        )

        assert first_result['should_update_club_statsbomb_id'] is True
        new_statsbomb_id = first_result['new_statsbomb_team_id']
        assert new_statsbomb_id == 779

        # Simulate updating database with new_statsbomb_team_id
        # Now run subsequent match with the ID set
        second_result = identify_teams_and_opponent(
            club_name="Argentina",
            club_statsbomb_team_id=new_statsbomb_id,  # Now set
            events=events,
            opponent_name="Australia",
            opponent_logo_url="https://example.com/australia.png"
        )

        assert second_result['should_update_club_statsbomb_id'] is False
        assert second_result['new_statsbomb_team_id'] is None
        assert second_result['our_team_id'] == 779
        assert second_result['our_team_name'] == "Argentina"
