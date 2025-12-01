"""
Event service for storing StatsBomb events.

Provides functions to store Pass, Shot, and Dribble events from StatsBomb data.
"""

from typing import List, Dict, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.event import Event
from app.models.match import Match


def parse_events_for_storage(events: List[dict]) -> dict:
    """
    Parse and filter events for storage (pure processing, no database).

    This is a helper function that filters events to only Pass (30), Shot (16),
    and Dribble (14) types, and extracts database fields for manual testing.

    Args:
        events: StatsBomb events array

    Returns:
        {
            'total_events': int,  # Total events in input
            'filtered_count': int,  # Events matching type filter
            'first_shot': {
                'raw': dict,  # Full event JSON
                'extracted': {
                    'player_name': str | None,
                    'statsbomb_player_id': int | None,
                    'team_name': str | None,
                    'statsbomb_team_id': int | None,
                    'event_type_name': str | None,
                    'position_name': str | None,
                    'minute': int | None,
                    'second': int | None,
                    'period': int | None
                }
            } | None,
            'first_pass': { ... } | None,
            'first_dribble': { ... } | None
        }
    """
    # Filter to only Pass (30), Shot (16), Dribble (14)
    filtered_events = [
        event for event in events
        if event.get('type', {}).get('id') in [14, 16, 30]
    ]

    # Find first occurrence of each type
    first_shot = None
    first_pass = None
    first_dribble = None

    for event in filtered_events:
        type_id = event.get('type', {}).get('id')

        if type_id == 16 and first_shot is None:
            first_shot = _extract_event_data(event)
        elif type_id == 30 and first_pass is None:
            first_pass = _extract_event_data(event)
        elif type_id == 14 and first_dribble is None:
            first_dribble = _extract_event_data(event)

        # Stop once we have all three
        if first_shot and first_pass and first_dribble:
            break

    return {
        'total_events': len(events),
        'filtered_count': len(filtered_events),
        'first_shot': first_shot,
        'first_pass': first_pass,
        'first_dribble': first_dribble
    }


def _extract_event_data(event: dict) -> dict:
    """
    Extract database fields from a single event.

    Helper function to extract all fields needed for database storage.
    Uses safe .get() to handle missing fields (returns None).

    Args:
        event: Single StatsBomb event

    Returns:
        {
            'raw': dict,  # Full event JSON
            'extracted': {
                'player_name': str | None,
                'statsbomb_player_id': int | None,
                'team_name': str | None,
                'statsbomb_team_id': int | None,
                'event_type_name': str | None,
                'position_name': str | None,
                'minute': int | None,
                'second': int | None,
                'period': int | None
            }
        }
    """
    return {
        'raw': event,
        'extracted': {
            'player_name': event.get('player', {}).get('name'),
            'statsbomb_player_id': event.get('player', {}).get('id'),
            'team_name': event.get('team', {}).get('name'),
            'statsbomb_team_id': event.get('team', {}).get('id'),
            'event_type_name': event.get('type', {}).get('name'),
            'position_name': event.get('position', {}).get('name'),
            'minute': event.get('minute'),
            'second': event.get('second'),
            'period': event.get('period')
        }
    }


def insert_events(
    db: Session,
    match_id: UUID,
    events: List[dict]
) -> int:
    """
    Insert Pass, Shot, and Dribble events into database.

    Filters events to only store Pass (type.id=30), Shot (type.id=16),
    and Dribble (type.id=14) events. Uses batch inserts (500 per batch)
    for performance.

    Args:
        db: Database session
        match_id: Match ID (UUID)
        events: StatsBomb events array

    Returns:
        int: Count of events inserted

    Raises:
        ValueError: If match not found or no filtered events
    """
    # Step 1: Validate match exists
    match = db.query(Match).filter(Match.match_id == match_id).first()
    if not match:
        raise ValueError(f"Match with ID {match_id} not found")

    # Step 2: Filter to only Pass (30), Shot (16), Dribble (14)
    filtered_events = [
        event for event in events
        if event.get('type', {}).get('id') in [14, 16, 30]
    ]

    # Step 3: Validate filtered count
    if len(filtered_events) == 0:
        raise ValueError("No Pass, Shot, or Dribble events found in data")

    # Step 4: Batch insert (500 events per batch)
    batch_size = 500
    event_count = 0

    for i, event in enumerate(filtered_events):
        # Extract fields using safe .get()
        player_name = event.get('player', {}).get('name')
        statsbomb_player_id = event.get('player', {}).get('id')
        team_name = event.get('team', {}).get('name')
        statsbomb_team_id = event.get('team', {}).get('id')
        event_type_name = event.get('type', {}).get('name')
        position_name = event.get('position', {}).get('name')
        minute = event.get('minute')
        second = event.get('second')
        period = event.get('period')

        # Create Event record
        event_record = Event(
            match_id=match_id,
            statsbomb_player_id=statsbomb_player_id,
            statsbomb_team_id=statsbomb_team_id,
            player_name=player_name,
            team_name=team_name,
            event_type_name=event_type_name,
            position_name=position_name,
            minute=minute,
            second=second,
            period=period,
            event_data=event  # Full JSON stored as JSONB
        )

        db.add(event_record)
        event_count += 1

        # Flush every 500 events (better memory management)
        if (i + 1) % batch_size == 0:
            db.flush()

    # Final flush for remaining events (caller manages commit)
    db.flush()

    return event_count


# Manual testing CLI
if __name__ == "__main__":
    import json
    from pathlib import Path

    print("=== Event Parser - Manual Testing ===\n")

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

    # Parse events
    print("="*70)
    try:
        result = parse_events_for_storage(events)

        # Display summary
        print(f"\n📊 SUMMARY")
        print("="*70)
        print(f"Total events in file: {result['total_events']}")
        print(f"Filtered events (Pass/Shot/Dribble): {result['filtered_count']}")
        print()

        # Display first shot
        if result['first_shot']:
            print(f"\n🎯 FIRST SHOT EVENT")
            print("="*70)
            extracted = result['first_shot']['extracted']
            print(f"Player: {extracted['player_name']} (ID: {extracted['statsbomb_player_id']})")
            print(f"Team: {extracted['team_name']} (ID: {extracted['statsbomb_team_id']})")
            print(f"Position: {extracted['position_name']}")
            print(f"Time: {extracted['minute']}:{extracted['second']} (Period {extracted['period']})")
            print(f"Type: {extracted['event_type_name']}")
            print(f"\nRaw JSON (first 500 chars):")
            print(json.dumps(result['first_shot']['raw'], indent=2)[:500] + "...")
        else:
            print("\n🎯 FIRST SHOT EVENT: None found")

        # Display first pass
        if result['first_pass']:
            print(f"\n⚽ FIRST PASS EVENT")
            print("="*70)
            extracted = result['first_pass']['extracted']
            print(f"Player: {extracted['player_name']} (ID: {extracted['statsbomb_player_id']})")
            print(f"Team: {extracted['team_name']} (ID: {extracted['statsbomb_team_id']})")
            print(f"Position: {extracted['position_name']}")
            print(f"Time: {extracted['minute']}:{extracted['second']} (Period {extracted['period']})")
            print(f"Type: {extracted['event_type_name']}")
            print(f"\nRaw JSON (first 500 chars):")
            print(json.dumps(result['first_pass']['raw'], indent=2)[:500] + "...")
        else:
            print("\n⚽ FIRST PASS EVENT: None found")

        # Display first dribble
        if result['first_dribble']:
            print(f"\n🏃 FIRST DRIBBLE EVENT")
            print("="*70)
            extracted = result['first_dribble']['extracted']
            print(f"Player: {extracted['player_name']} (ID: {extracted['statsbomb_player_id']})")
            print(f"Team: {extracted['team_name']} (ID: {extracted['statsbomb_team_id']})")
            print(f"Position: {extracted['position_name']}")
            print(f"Time: {extracted['minute']}:{extracted['second']} (Period {extracted['period']})")
            print(f"Type: {extracted['event_type_name']}")
            print(f"\nRaw JSON (first 500 chars):")
            print(json.dumps(result['first_dribble']['raw'], indent=2)[:500] + "...")
        else:
            print("\n🏃 FIRST DRIBBLE EVENT: None found")

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
