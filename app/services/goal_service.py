"""
Goal service for extracting and storing goal events from StatsBomb data.

Provides functions to parse goal events (Shot events with Goal outcome)
and store them in the goals table with scorer information and timing.
"""

from typing import List, Dict, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.goal import Goal
from app.models.match import Match


def parse_goals_from_events(
    events: List[dict],
    our_club_statsbomb_id: int,
    opponent_statsbomb_id: int
) -> List[dict]:
    """
    Parse and extract goal events from StatsBomb events (pure processing, no database).

    This is a helper function that filters Shot events with Goal outcome (id=97)
    and extracts scorer information, timing, and team identification.

    Args:
        events: StatsBomb events array
        our_club_statsbomb_id: StatsBomb team ID for our club
        opponent_statsbomb_id: StatsBomb team ID for opponent club

    Returns:
        List of goal dicts with fields:
        [
            {
                'scorer_name': str,  # Player name or "Unknown" if missing
                'minute': int,       # Match minute
                'second': int | None,  # Match second (None if missing)
                'is_our_goal': bool  # True if scored by our team
            },
            ...
        ]

    Notes:
        - Only includes Shot events (type.id=16) with Goal outcome (shot.outcome.id=97)
        - Excludes penalty shootout goals (period=5)
        - Uses team.id to determine which team scored
        - Uses "Unknown" for scorer_name if player field is missing
        - Allows None for second field if missing in event data
    """
    goals = []

    for event in events:
        # Filter 1: Must be Shot event (type.id = 16)
        if event.get('type', {}).get('id') != 16:
            continue

        # Filter 2: Must have Goal outcome (shot.outcome.id = 97)
        if event.get('shot', {}).get('outcome', {}).get('id') != 97:
            continue

        # Filter 3: Exclude penalty shootout (period = 5)
        if event.get('period') == 5:
            continue

        # Extract fields
        scorer_name = event.get('player', {}).get('name')
        if scorer_name is None:
            scorer_name = "Unknown"

        minute = event.get('minute')
        second = event.get('second')  # Can be None

        # Determine if our goal using team.id
        team_id = event.get('team', {}).get('id')
        is_our_goal = (team_id == our_club_statsbomb_id)

        goals.append({
            'scorer_name': scorer_name,
            'minute': minute,
            'second': second,
            'is_our_goal': is_our_goal
        })

    return goals


def insert_goals(
    db: Session,
    match_id: UUID,
    events: List[dict],
    our_club_statsbomb_id: int,
    opponent_statsbomb_id: int
) -> int:
    """
    Insert goal events into database.

    Extracts goals from Shot events with Goal outcome and stores them
    in the goals table with scorer information and timing.

    Args:
        db: Database session
        match_id: Match ID (UUID)
        events: StatsBomb events array
        our_club_statsbomb_id: StatsBomb team ID for our club
        opponent_statsbomb_id: StatsBomb team ID for opponent club

    Returns:
        int: Count of goals inserted

    Raises:
        ValueError: If match not found
    """
    # Step 1: Validate match exists
    match = db.query(Match).filter(Match.match_id == match_id).first()
    if not match:
        raise ValueError(f"Match with ID {match_id} not found")

    # Step 2: Parse goals from events
    goals_data = parse_goals_from_events(
        events=events,
        our_club_statsbomb_id=our_club_statsbomb_id,
        opponent_statsbomb_id=opponent_statsbomb_id
    )

    # Step 3: Insert goals
    goal_count = 0
    for goal_data in goals_data:
        goal_record = Goal(
            match_id=match_id,
            scorer_name=goal_data['scorer_name'],
            minute=goal_data['minute'],
            second=goal_data['second'],
            is_our_goal=goal_data['is_our_goal']
        )
        db.add(goal_record)
        goal_count += 1

    # Step 4: Commit all goals
    db.commit()

    return goal_count


# Manual testing CLI
if __name__ == "__main__":
    import json
    from pathlib import Path

    print("=== Goal Parser - Manual Testing ===\n")

    # Get JSON file path
    default_path = "data/3869685.json"
    json_path = input(f"Enter JSON file path (default: {default_path}): ").strip()
    if not json_path:
        json_path = default_path

    # Load events
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            events = json.load(f)
        print(f"✓ Loaded {len(events)} events from {json_path}\n")
    except FileNotFoundError:
        print(f"✗ Error: File not found: {json_path}")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Error: Invalid JSON: {e}")
        exit(1)

    # Get team IDs
    print("Enter StatsBomb team IDs:")
    try:
        our_club_id = int(input("  Our club StatsBomb ID (default: 217 for Barcelona): ").strip() or "217")
        opponent_id = int(input("  Opponent StatsBomb ID (default: 206 for Deportivo Alavés): ").strip() or "206")
    except ValueError:
        print("✗ Error: Team IDs must be integers")
        exit(1)

    # Parse goals
    print("\n" + "="*70)
    try:
        goals = parse_goals_from_events(
            events=events,
            our_club_statsbomb_id=our_club_id,
            opponent_statsbomb_id=opponent_id
        )

        # Display summary
        print(f"\n📊 SUMMARY")
        print("="*70)
        print(f"Total events in file: {len(events)}")
        print(f"Total goals found: {len(goals)}")

        # Count goals by team
        our_goals = [g for g in goals if g['is_our_goal']]
        opponent_goals = [g for g in goals if not g['is_our_goal']]
        print(f"  Our goals: {len(our_goals)}")
        print(f"  Opponent goals: {len(opponent_goals)}")
        print()

        # Display all goals
        if len(goals) > 0:
            print(f"\n⚽ ALL GOALS")
            print("="*70)
            for i, goal in enumerate(goals, 1):
                team_label = "Our Team" if goal['is_our_goal'] else "Opponent"
                second_str = f":{goal['second']}" if goal['second'] is not None else ""
                print(f"\nGoal #{i} ({team_label}):")
                print(f"  Scorer: {goal['scorer_name']}")
                print(f"  Time: {goal['minute']}{second_str}'")
                print(f"  Is Our Goal: {goal['is_our_goal']}")
        else:
            print("\n⚽ ALL GOALS: No goals found in match")

        print("\n" + "="*70)
        print("✓ Success!")

    except ValueError as e:
        print(f"\n✗ Error: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
