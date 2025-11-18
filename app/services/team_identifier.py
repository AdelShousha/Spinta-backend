"""
Team identification service.

This module provides pure processing logic to identify our team and opponent team
from StatsBomb Starting XI events using fuzzy name matching.
"""

from typing import List, Optional
import difflib


def fuzzy_match_team_name(club_name: str, team_1_name: str, team_2_name: str) -> Optional[int]:
    """
    Fuzzy match club name to one of two team names.

    Match priority:
    1. Exact match (case-insensitive)
    2. Substring match (handles "Thunder United" vs "Thunder United FC")
    3. Fuzzy match with 80% similarity threshold

    Args:
        club_name: Our club's name from database
        team_1_name: First team name from Starting XI event
        team_2_name: Second team name from Starting XI event

    Returns:
        1 if club_name matches team_1_name
        2 if club_name matches team_2_name
        None if no match found
    """
    club_lower = club_name.lower()
    team1_lower = team_1_name.lower()
    team2_lower = team_2_name.lower()

    # Try exact match first
    if club_lower == team1_lower:
        return 1
    if club_lower == team2_lower:
        return 2

    # Try substring match (handles "Thunder United" vs "Thunder United FC")
    if club_lower in team1_lower or team1_lower in club_lower:
        return 1
    if club_lower in team2_lower or team2_lower in club_lower:
        return 2

    # Try fuzzy match with 80% similarity threshold
    sim1 = difflib.SequenceMatcher(None, club_lower, team1_lower).ratio()
    sim2 = difflib.SequenceMatcher(None, club_lower, team2_lower).ratio()

    if sim1 > 0.8 and sim1 > sim2:
        return 1
    if sim2 > 0.8:
        return 2

    return None  # No match


def identify_teams(club_name: str, events: List[dict]) -> dict:
    """
    Identify our team and opponent team from Starting XI events.

    Pure processing logic - extracts team information from event data using
    fuzzy name matching. No database operations.

    Args:
        club_name: Our club's name from database (e.g., "Argentina")
        events: Full StatsBomb events array

    Returns:
        {
            'our_club_statsbomb_team_id': int,
            'our_club_name': str,
            'opponent_statsbomb_team_id': int,
            'opponent_name': str
        }

    Raises:
        ValueError: If validation fails or no match found
    """
    # Step 1: Extract Starting XI events
    starting_xi_events = [e for e in events if e.get('type', {}).get('id') == 35]

    # Validation: Must have exactly 2 events
    if len(starting_xi_events) != 2:
        raise ValueError(
            f"Expected 2 Starting XI events, found {len(starting_xi_events)}"
        )

    # Validation: Each must have 11 players
    for event in starting_xi_events:
        lineup = event.get('tactics', {}).get('lineup', [])
        lineup_count = len(lineup)
        team_name = event.get('team', {}).get('name', 'Unknown')
        if lineup_count != 11:
            raise ValueError(
                f"Starting XI for {team_name} has {lineup_count} players (expected 11)"
            )

    # Step 2: Extract team information from both events
    team_1_id = starting_xi_events[0]['team']['id']
    team_1_name = starting_xi_events[0]['team']['name']

    team_2_id = starting_xi_events[1]['team']['id']
    team_2_name = starting_xi_events[1]['team']['name']

    # Step 3: Identify our team using fuzzy matching
    matched = fuzzy_match_team_name(club_name, team_1_name, team_2_name)

    if matched == 1:
        our_club_statsbomb_team_id = team_1_id
        our_club_name = team_1_name
        opponent_statsbomb_team_id = team_2_id
        opponent_name = team_2_name
    elif matched == 2:
        our_club_statsbomb_team_id = team_2_id
        our_club_name = team_2_name
        opponent_statsbomb_team_id = team_1_id
        opponent_name = team_1_name
    else:
        raise ValueError(
            f"Cannot match your club name '{club_name}' to teams in event data: "
            f"'{team_1_name}', '{team_2_name}'"
        )

    # Return result
    return {
        'our_club_statsbomb_team_id': our_club_statsbomb_team_id,
        'our_club_name': our_club_name,
        'opponent_statsbomb_team_id': opponent_statsbomb_team_id,
        'opponent_name': opponent_name
    }


# Interactive manual testing
if __name__ == "__main__":
    import json
    import sys

    print("=" * 60)
    print("Team Identification - Manual Test")
    print("=" * 60)

    # Interactive input
    try:
        json_file_path = input("\nEnter path to JSON file (or press Enter for default): ").strip()
        if not json_file_path:
            json_file_path = "docs/15946.json"

        club_name = input("Enter our club name: ").strip()
        if not club_name:
            print("Error: Club name is required")
            sys.exit(1)

        print("\n" + "-" * 60)
        print(f"Loading events from: {json_file_path}")
        print(f"Club name: {club_name}")
        print("-" * 60)

        # Load events from file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            events = json.load(f)

        print(f"✓ Loaded {len(events)} events")

        # Run function
        print("\nProcessing...")
        result = identify_teams(club_name, events)

        # Print result
        print("\n" + "=" * 60)
        print("RESULT:")
        print("=" * 60)
        print(json.dumps(result, indent=2))
        print("=" * 60)
        print("✓ Success!")

    except FileNotFoundError:
        print(f"\n✗ Error: File '{json_file_path}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\n✗ Error: Invalid JSON in '{json_file_path}': {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
