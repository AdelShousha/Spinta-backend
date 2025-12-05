"""
Match service.

This module provides match-related operations including score validation
and match record creation.
"""

from typing import List, Optional
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.club import Club
from app.models.opponent_club import OpponentClub


def count_goals_from_events(
    events: List[dict],
    our_club_statsbomb_team_id: int,
    opponent_statsbomb_team_id: int
) -> dict:
    """
    Count goals from StatsBomb events for both teams.

    This function parses Shot events (type 16) with Goal outcomes (outcome 97)
    and counts goals for each team based on possession_team.id.

    IMPORTANT: Excludes penalty shootout goals (period 5).
    Only counts goals from regular time and extra time (periods 1-4).
    Match result is determined by score at end of regular/extra time, not penalty shootout.

    Args:
        events: Full StatsBomb events array
        our_club_statsbomb_team_id: Our club's StatsBomb team ID
        opponent_statsbomb_team_id: Opponent's StatsBomb team ID

    Returns:
        {
            'our_goals': int,
            'opponent_goals': int
        }
    """
    our_goals = 0
    opponent_goals = 0

    for event in events:
        # Skip penalty shootout (period 5)
        # Match result is based on regular/extra time only
        if event.get('period') == 5:
            continue

        # Check if this is a Shot event (type 16)
        if event.get('type', {}).get('id') != 16:
            continue

        # Check if the shot resulted in a Goal (outcome 97)
        shot_outcome_id = event.get('shot', {}).get('outcome', {}).get('id')
        if shot_outcome_id != 97:
            continue

        # Determine which team scored based on possession_team.id
        possession_team_id = event.get('team', {}).get('id')

        if possession_team_id == our_club_statsbomb_team_id:
            our_goals += 1
        elif possession_team_id == opponent_statsbomb_team_id:
            opponent_goals += 1

    return {
        'our_goals': our_goals,
        'opponent_goals': opponent_goals
    }


def create_match_record(
    db: Session,
    club_id: UUID,
    opponent_club_id: UUID,
    match_date: str,
    our_score: int,
    opponent_score: int,
    opponent_name: str,
    events: List[dict]
) -> UUID:
    """
    Create match record with score validation from StatsBomb events.

    This function:
    1. Retrieves StatsBomb team IDs from database
    2. Counts goals from events
    3. Validates user-provided scores match event data
    4. Calculates match result (W/D/L)
    5. Creates match record

    Parameter Sources:
    - club_id: Query clubs table using our_club_statsbomb_team_id from Iteration 1
    - opponent_club_id: Output from get_or_create_opponent_club() (Iteration 2)
    - match_date: From request body
    - our_score: From request body (user input)
    - opponent_score: From request body (user input)
    - opponent_name: From request body
    - events: From request body (StatsBomb events array)

    Args:
        db: Database session
        club_id: Our club's ID (UUID)
        opponent_club_id: Opponent club's ID (UUID)
        match_date: Match date (YYYY-MM-DD string)
        our_score: Our club's score (user input)
        opponent_score: Opponent's score (user input)
        opponent_name: Opponent name
        events: StatsBomb events array

    Returns:
        match_id (UUID)

    Raises:
        ValueError: If scores don't match event data
    """
    # Step 1: Get StatsBomb team IDs from database
    club = db.query(Club).filter(Club.club_id == club_id).first()
    if not club:
        raise ValueError(f"Club with ID {club_id} not found")

    opponent_club = db.query(OpponentClub).filter(
        OpponentClub.opponent_club_id == opponent_club_id
    ).first()
    if not opponent_club:
        raise ValueError(f"Opponent club with ID {opponent_club_id} not found")

    our_club_statsbomb_team_id = club.statsbomb_team_id
    opponent_statsbomb_team_id = opponent_club.statsbomb_team_id

    # Step 2: Count goals from events
    goal_counts = count_goals_from_events(
        events=events,
        our_club_statsbomb_team_id=our_club_statsbomb_team_id,
        opponent_statsbomb_team_id=opponent_statsbomb_team_id
    )

    # Step 3: Validate scores match event data
    if goal_counts['our_goals'] != our_score or goal_counts['opponent_goals'] != opponent_score:
        raise ValueError(
            f"Score mismatch: Event data shows {goal_counts['our_goals']}-{goal_counts['opponent_goals']}, "
            f"but user provided {our_score}-{opponent_score}"
        )

    # Step 4: Calculate result
    if our_score > opponent_score:
        result = 'W'
    elif our_score < opponent_score:
        result = 'L'
    else:
        result = 'D'

    # Step 5: Create match record
    match = Match(
        club_id=club_id,
        opponent_club_id=opponent_club_id,
        opponent_name=opponent_name,
        match_date=date.fromisoformat(match_date),  # Convert string to date
        our_score=our_score,
        opponent_score=opponent_score,
        result=result
    )

    db.add(match)
    db.flush()  # Flush to database without committing (caller manages transaction)


    return match.match_id


# Interactive manual testing
# run python -m app.services.match_service
if __name__ == "__main__":
    import json
    import sys

    print("=" * 60)
    print("Goal Counting - Manual Test")
    print("=" * 60)

    try:
        json_file_path = input(
            "\nEnter path to JSON file (or press Enter for default): ").strip()
        if not json_file_path:
            json_file_path = "docs/15946.json"

        our_team_id_input = input("Enter our team StatsBomb ID: ").strip()
        if not our_team_id_input:
            print("Error: Our team StatsBomb ID is required")
            sys.exit(1)
        our_team_id = int(our_team_id_input)

        opponent_team_id_input = input(
            "Enter opponent team StatsBomb ID: ").strip()
        if not opponent_team_id_input:
            print("Error: Opponent team StatsBomb ID is required")
            sys.exit(1)
        opponent_team_id = int(opponent_team_id_input)

        print("\n" + "-" * 60)
        print(f"Loading events from: {json_file_path}")
        print(f"Our team StatsBomb ID: {our_team_id}")
        print(f"Opponent team StatsBomb ID: {opponent_team_id}")
        print("-" * 60)

        # Load events from file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            events = json.load(f)

        print(f"✓ Loaded {len(events)} events")

        # Run function
        print("\nCounting goals...")
        result = count_goals_from_events(events, our_team_id, opponent_team_id)

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
