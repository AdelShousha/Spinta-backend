"""
Team identification and opponent club handling service.

This module provides functions to identify our team and opponent team from
StatsBomb Starting XI events, with smart matching logic for first vs subsequent matches.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
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


def get_or_create_opponent_club(
    statsbomb_team_id: int,
    opponent_name: str,
    opponent_logo_url: str,
    existing_opponents: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Get or create opponent club using ONLY statsbomb_team_id for matching.

    This function simulates database operations for testing purposes.
    In production, this will be integrated with SQLAlchemy ORM.

    Args:
        statsbomb_team_id: StatsBomb team ID from event data
        opponent_name: Opponent name from request body
        opponent_logo_url: Opponent logo URL from request body
        existing_opponents: Simulated existing opponents (for testing)

    Returns:
        {
            'opponent_club_id': UUID,
            'statsbomb_team_id': int,
            'opponent_name': str,
            'logo_url': str,
            'is_new': bool
        }
    """
    # Simulate: SELECT opponent_club_id FROM opponent_clubs
    #           WHERE statsbomb_team_id = :statsbomb_team_id
    if existing_opponents:
        for opponent in existing_opponents:
            if opponent.get('statsbomb_team_id') == statsbomb_team_id:
                return {
                    'opponent_club_id': opponent['opponent_club_id'],
                    'statsbomb_team_id': opponent['statsbomb_team_id'],
                    'opponent_name': opponent['opponent_name'],
                    'logo_url': opponent['logo_url'],
                    'is_new': False
                }

    # Not found - create new opponent club
    # Simulate: INSERT INTO opponent_clubs (
    #   opponent_club_id, statsbomb_team_id, opponent_name, logo_url, created_at
    # ) VALUES (...)
    new_opponent_club_id = uuid4()

    return {
        'opponent_club_id': new_opponent_club_id,
        'statsbomb_team_id': statsbomb_team_id,
        'opponent_name': opponent_name,
        'logo_url': opponent_logo_url,
        'is_new': True
    }


def identify_teams_and_opponent(
    club_name: str,
    club_statsbomb_team_id: Optional[int],
    events: List[dict],
    opponent_name: str,
    opponent_logo_url: str,
    existing_opponents: Optional[List[Dict[str, Any]]] = None
) -> dict:
    """
    Identify our team and opponent team from Starting XI events.

    This function handles both first match (fuzzy matching) and subsequent matches
    (direct ID matching). It also handles get/create logic for opponent clubs.

    Args:
        club_name: Our club's name from database (e.g., "Argentina")
        club_statsbomb_team_id: Our club's StatsBomb team ID (None for first match)
        events: Full StatsBomb events array
        opponent_name: Opponent name from request body
        opponent_logo_url: Opponent logo URL from request body
        existing_opponents: Simulated existing opponents (for testing)

    Returns:
        {
            'our_team_id': int,
            'our_team_name': str,
            'opponent_club_id': UUID,
            'opponent_team_id': int,
            'opponent_team_name': str,
            'should_update_club_statsbomb_id': bool,
            'new_statsbomb_team_id': int or None
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

    # Step 3: Identify our team (smart matching)
    if club_statsbomb_team_id is None:
        # First match: fuzzy match by name
        matched = fuzzy_match_team_name(club_name, team_1_name, team_2_name)

        if matched == 1:
            our_team_id = team_1_id
            our_team_name = team_1_name
            opponent_team_id = team_2_id
            opponent_team_name = team_2_name
        elif matched == 2:
            our_team_id = team_2_id
            our_team_name = team_2_name
            opponent_team_id = team_1_id
            opponent_team_name = team_1_name
        else:
            raise ValueError(
                f"Cannot match your club name '{club_name}' to teams in event data: "
                f"'{team_1_name}', '{team_2_name}'"
            )

        should_update = True
        new_statsbomb_team_id = our_team_id

    else:
        # Subsequent match: direct match by ID
        if club_statsbomb_team_id == team_1_id:
            our_team_id = team_1_id
            our_team_name = team_1_name
            opponent_team_id = team_2_id
            opponent_team_name = team_2_name
        elif club_statsbomb_team_id == team_2_id:
            our_team_id = team_2_id
            our_team_name = team_2_name
            opponent_team_id = team_1_id
            opponent_team_name = team_1_name
        else:
            raise ValueError(
                f"Club's statsbomb_team_id {club_statsbomb_team_id} doesn't match "
                f"either team in events: {team_1_id} ({team_1_name}), "
                f"{team_2_id} ({team_2_name})"
            )

        should_update = False
        new_statsbomb_team_id = None

    # Step 4: Get or create opponent club (match by StatsBomb team ID ONLY)
    opponent_club_data = get_or_create_opponent_club(
        statsbomb_team_id=opponent_team_id,
        opponent_name=opponent_name,
        opponent_logo_url=opponent_logo_url,
        existing_opponents=existing_opponents
    )

    # Return result
    return {
        'our_team_id': our_team_id,
        'our_team_name': our_team_name,
        'opponent_club_id': opponent_club_data['opponent_club_id'],
        'opponent_team_id': opponent_team_id,
        'opponent_team_name': opponent_team_name,
        'should_update_club_statsbomb_id': should_update,
        'new_statsbomb_team_id': new_statsbomb_team_id
    }


# Manual testing
if __name__ == "__main__":
    import json
    import sys

    # Usage: python app/services/team_identifier.py [events_file]

    # Load events from file
    events_file = sys.argv[1] if len(sys.argv) > 1 else "docs/15946.json"

    try:
        with open(events_file, 'r', encoding='utf-8') as f:
            events = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{events_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{events_file}': {e}")
        sys.exit(1)

    # Test parameters (modify these to test different scenarios)
    club_name = "Argentina"
    club_statsbomb_team_id = None  # Change to 779 to test subsequent match
    opponent_name = "Australia"
    opponent_logo_url = "https://example.com/australia.png"

    print("=" * 60)
    print("Testing Team Identification")
    print("=" * 60)
    print(f"Club name: {club_name}")
    print(f"Club StatsBomb ID: {club_statsbomb_team_id}")
    print(f"Events file: {events_file}")
    print(f"Opponent name (from request): {opponent_name}")
    print(f"Opponent logo URL (from request): {opponent_logo_url}")
    print("-" * 60)

    try:
        # Run function
        result = identify_teams_and_opponent(
            club_name=club_name,
            club_statsbomb_team_id=club_statsbomb_team_id,
            events=events,
            opponent_name=opponent_name,
            opponent_logo_url=opponent_logo_url
        )

        # Print result
        print("\nResult:")
        print(json.dumps(result, indent=2, default=str))
        print("\n" + "=" * 60)
        print("Success!")
        print("=" * 60)

    except ValueError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
