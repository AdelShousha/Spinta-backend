"""
Tests for team identification service.
"""

import pytest
from app.services.team_identifier import (
    fuzzy_match_team_name,
    identify_teams
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
    """Test team identification logic."""

    def test_exact_name_match(self):
        """Test with exact name match (first match)."""
        events = create_sample_events()
        result = identify_teams(
            club_name="Argentina",
            events=events
        )

        assert result['our_club_statsbomb_team_id'] == 779
        assert result['our_club_name'] == "Argentina"
        assert result['opponent_statsbomb_team_id'] == 792
        assert result['opponent_name'] == "Australia"
        assert result['should_update_statsbomb_id'] is True
        assert result['new_statsbomb_team_id'] == 779

    def test_substring_match(self):
        """Test with substring match."""
        events = create_sample_events(team_1_name="Argentina FC")
        result = identify_teams(
            club_name="Argentina",
            events=events
        )

        assert result['our_club_statsbomb_team_id'] == 779
        assert result['our_club_name'] == "Argentina FC"
        assert result['opponent_statsbomb_team_id'] == 792
        assert result['opponent_name'] == "Australia"

    def test_fuzzy_match_80_percent(self):
        """Test with fuzzy match at 80% threshold."""
        # "Thunder United" vs "Thunder Utd" has ~85% similarity
        events = create_sample_events(
            team_1_id=779,
            team_1_name="Thunder Utd",
            team_2_id=792,
            team_2_name="Australia"
        )
        result = identify_teams(
            club_name="Thunder United",
            events=events
        )

        assert result['our_club_statsbomb_team_id'] == 779
        assert result['our_club_name'] == "Thunder Utd"

    def test_team_2_is_ours(self):
        """Test when our team is the second Starting XI event."""
        events = create_sample_events()
        result = identify_teams(
            club_name="Australia",
            events=events
        )

        assert result['our_club_statsbomb_team_id'] == 792
        assert result['our_club_name'] == "Australia"
        assert result['opponent_statsbomb_team_id'] == 779
        assert result['opponent_name'] == "Argentina"

    def test_no_match_error(self):
        """Test error when club name doesn't match either team."""
        events = create_sample_events()
        with pytest.raises(ValueError, match="Cannot match your club name"):
            identify_teams(
                club_name="Brazil",
                events=events
            )


class TestSubsequentMatches:
    """Test subsequent match scenarios with direct ID matching."""

    def test_subsequent_match_team_1(self):
        """Test subsequent match with direct ID match (team 1 is ours)."""
        events = create_sample_events()
        result = identify_teams(
            club_name="Argentina",
            events=events,
            club_statsbomb_team_id=779  # Already set from first match
        )

        assert result['our_club_statsbomb_team_id'] == 779
        assert result['our_club_name'] == "Argentina"
        assert result['opponent_statsbomb_team_id'] == 792
        assert result['opponent_name'] == "Australia"
        assert result['should_update_statsbomb_id'] is False
        assert result['new_statsbomb_team_id'] is None

    def test_subsequent_match_team_2(self):
        """Test subsequent match with direct ID match (team 2 is ours)."""
        events = create_sample_events()
        result = identify_teams(
            club_name="Australia",
            events=events,
            club_statsbomb_team_id=792
        )

        assert result['our_club_statsbomb_team_id'] == 792
        assert result['our_club_name'] == "Australia"
        assert result['opponent_statsbomb_team_id'] == 779
        assert result['opponent_name'] == "Argentina"
        assert result['should_update_statsbomb_id'] is False
        assert result['new_statsbomb_team_id'] is None

    def test_subsequent_match_id_not_found(self):
        """Test error when club_statsbomb_team_id doesn't match either team."""
        events = create_sample_events()
        with pytest.raises(ValueError, match="doesn't match either team"):
            identify_teams(
                club_name="Argentina",
                events=events,
                club_statsbomb_team_id=999  # Wrong ID
            )

    def test_subsequent_match_skips_fuzzy_matching(self):
        """Test that subsequent matches use direct ID matching, not fuzzy matching."""
        # Even with a completely different club name, it should match by ID
        events = create_sample_events()
        result = identify_teams(
            club_name="Completely Wrong Name",  # This would fail fuzzy matching
            events=events,
            club_statsbomb_team_id=779  # But ID matching works
        )

        assert result['our_club_statsbomb_team_id'] == 779
        assert result['our_club_name'] == "Argentina"  # Gets correct name from events
        assert result['should_update_statsbomb_id'] is False

    def test_first_then_subsequent_match_flow(self):
        """Test complete flow: first match then subsequent match."""
        events = create_sample_events()

        # First match (fuzzy matching)
        first_result = identify_teams(
            club_name="Argentina",
            events=events,
            club_statsbomb_team_id=None
        )

        assert first_result['should_update_statsbomb_id'] is True
        new_id = first_result['new_statsbomb_team_id']
        assert new_id == 779

        # Subsequent match (direct ID matching)
        second_result = identify_teams(
            club_name="Argentina",
            events=events,
            club_statsbomb_team_id=new_id  # Use ID from first match
        )

        assert second_result['should_update_statsbomb_id'] is False
        assert second_result['new_statsbomb_team_id'] is None
        assert second_result['our_club_statsbomb_team_id'] == 779


class TestValidationErrors:
    """Test validation error handling."""

    def test_error_not_two_starting_xi(self):
        """Test error when events don't have exactly 2 Starting XI events."""
        # Only 1 Starting XI event
        events = [create_starting_xi_event(779, "Argentina")]

        with pytest.raises(ValueError, match="Expected 2 Starting XI events, found 1"):
            identify_teams(
                club_name="Argentina",
                events=events
            )

    def test_error_three_starting_xi(self):
        """Test error when events have 3 Starting XI events."""
        events = [
            create_starting_xi_event(779, "Argentina"),
            create_starting_xi_event(792, "Australia"),
            create_starting_xi_event(800, "Brazil")
        ]

        with pytest.raises(ValueError, match="Expected 2 Starting XI events, found 3"):
            identify_teams(
                club_name="Argentina",
                events=events
            )

    def test_error_lineup_not_11_players(self):
        """Test error when lineup doesn't have 11 players."""
        events = [
            create_starting_xi_event(779, "Argentina", player_count=10),  # Only 10 players
            create_starting_xi_event(792, "Australia", player_count=11)
        ]

        with pytest.raises(ValueError, match="has 10 players \\(expected 11\\)"):
            identify_teams(
                club_name="Argentina",
                events=events
            )

    def test_error_both_lineups_wrong(self):
        """Test error when both lineups have wrong player count."""
        events = [
            create_starting_xi_event(779, "Argentina", player_count=12),
            create_starting_xi_event(792, "Australia", player_count=10)
        ]

        with pytest.raises(ValueError, match="expected 11"):
            identify_teams(
                club_name="Argentina",
                events=events
            )


class TestEndToEnd:
    """End-to-end tests with realistic StatsBomb data structure."""

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

        result = identify_teams(
            club_name="Argentina",
            events=events
        )

        assert result['our_club_statsbomb_team_id'] == 779
        assert result['our_club_name'] == "Argentina"
        assert result['opponent_statsbomb_team_id'] == 792
        assert result['opponent_name'] == "Australia"

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        events = create_sample_events()

        # lowercase club name
        result = identify_teams(
            club_name="argentina",
            events=events
        )

        assert result['our_club_statsbomb_team_id'] == 779
        assert result['our_club_name'] == "Argentina"

    def test_with_extra_events(self):
        """Test that function ignores non-Starting XI events."""
        events = [
            create_starting_xi_event(779, "Argentina"),
            {
                "id": "pass-event",
                "type": {"id": 30, "name": "Pass"},
                "team": {"id": 779, "name": "Argentina"}
            },
            {
                "id": "shot-event",
                "type": {"id": 16, "name": "Shot"},
                "team": {"id": 792, "name": "Australia"}
            },
            create_starting_xi_event(792, "Australia"),
            {
                "id": "tackle-event",
                "type": {"id": 4, "name": "Tackle"},
                "team": {"id": 779, "name": "Argentina"}
            }
        ]

        result = identify_teams(
            club_name="Argentina",
            events=events
        )

        # Should correctly extract teams despite extra events
        assert result['our_club_statsbomb_team_id'] == 779
        assert result['opponent_statsbomb_team_id'] == 792
