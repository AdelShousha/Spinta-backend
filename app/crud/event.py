"""
CRUD operations for Event model.

Functions:
- create_event: Create single event record
- create_events_bulk: Bulk insert events (efficient for ~3,000 events per match)
- get_events_by_match: Get all events for a match
- get_events_by_player: Get events for a specific player
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.event import Event


def create_event(
    db: Session,
    match_id: str,
    event_data: Dict[str, Any],
    statsbomb_player_id: Optional[int] = None,
    statsbomb_team_id: Optional[int] = None,
    player_name: Optional[str] = None,
    team_name: Optional[str] = None,
    event_type_name: Optional[str] = None,
    position_name: Optional[str] = None,
    minute: Optional[int] = None,
    second: Optional[int] = None,
    period: Optional[int] = None
) -> Event:
    """
    Create a single event record.

    Args:
        db: Database session
        match_id: UUID of the match
        event_data: Full event JSON data
        statsbomb_player_id: Optional StatsBomb player ID
        statsbomb_team_id: Optional StatsBomb team ID
        player_name: Optional player name
        team_name: Optional team name
        event_type_name: Optional event type (e.g., 'Pass', 'Shot')
        position_name: Optional player position
        minute: Optional minute of event
        second: Optional second within minute
        period: Optional match period

    Returns:
        Created Event instance

    Example:
        >>> event = create_event(
        ...     db,
        ...     match_id="550e8400-...",
        ...     event_data={"type": "Pass", "location": [50, 40]},
        ...     statsbomb_player_id=456,
        ...     event_type_name="Pass",
        ...     minute=15
        ... )
    """
    event = Event(
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
        event_data=event_data,
        created_at=datetime.now(timezone.utc)
    )

    db.add(event)
    db.flush()
    db.refresh(event)

    return event


def create_events_bulk(
    db: Session,
    match_id: str,
    events_data: List[Dict[str, Any]]
) -> int:
    """
    Bulk insert events for a match (efficient for ~3,000 events).

    This uses SQLAlchemy's bulk_insert_mappings for performance.

    Args:
        db: Database session
        match_id: UUID of the match
        events_data: List of event dictionaries with keys:
            - event_data: Full event JSON
            - statsbomb_player_id: Optional int
            - statsbomb_team_id: Optional int
            - player_name: Optional str
            - team_name: Optional str
            - event_type_name: Optional str
            - position_name: Optional str
            - minute: Optional int
            - second: Optional int
            - period: Optional int

    Returns:
        Number of events created

    Example:
        >>> events = [
        ...     {
        ...         "event_data": {"type": "Pass"},
        ...         "statsbomb_player_id": 456,
        ...         "event_type_name": "Pass",
        ...         "minute": 1
        ...     },
        ...     # ... 2,999 more events
        ... ]
        >>> count = create_events_bulk(db, "550e8400-...", events)
        >>> print(f"Created {count} events")
    """
    now = datetime.now(timezone.utc)

    # Prepare bulk insert data
    bulk_data = []
    for event_dict in events_data:
        bulk_data.append({
            "match_id": match_id,
            "statsbomb_player_id": event_dict.get("statsbomb_player_id"),
            "statsbomb_team_id": event_dict.get("statsbomb_team_id"),
            "player_name": event_dict.get("player_name"),
            "team_name": event_dict.get("team_name"),
            "event_type_name": event_dict.get("event_type_name"),
            "position_name": event_dict.get("position_name"),
            "minute": event_dict.get("minute"),
            "second": event_dict.get("second"),
            "period": event_dict.get("period"),
            "event_data": event_dict.get("event_data"),
            "created_at": now
        })

    # Bulk insert
    db.bulk_insert_mappings(Event, bulk_data)
    db.flush()

    return len(bulk_data)


def get_events_by_match(
    db: Session,
    match_id: str,
    event_type: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Event]:
    """
    Get all events for a specific match.

    Args:
        db: Database session
        match_id: Match UUID
        event_type: Optional filter by event type (e.g., 'Pass', 'Shot')
        limit: Optional limit on number of results

    Returns:
        List of Event instances ordered by period, minute, second

    Example:
        >>> events = get_events_by_match(db, "550e8400-...", event_type="Shot")
        >>> for event in events:
        ...     print(f"{event.minute}' - {event.event_type_name}")
    """
    query = db.query(Event).filter(Event.match_id == match_id)

    if event_type:
        query = query.filter(Event.event_type_name == event_type)

    query = query.order_by(Event.period, Event.minute, Event.second)

    if limit:
        query = query.limit(limit)

    return query.all()


def get_events_by_player(
    db: Session,
    statsbomb_player_id: int,
    match_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Event]:
    """
    Get events for a specific player.

    Args:
        db: Database session
        statsbomb_player_id: StatsBomb player ID
        match_id: Optional filter by specific match
        event_type: Optional filter by event type
        limit: Optional limit on number of results

    Returns:
        List of Event instances

    Example:
        >>> events = get_events_by_player(
        ...     db,
        ...     statsbomb_player_id=456,
        ...     event_type="Pass"
        ... )
    """
    query = db.query(Event).filter(Event.statsbomb_player_id == statsbomb_player_id)

    if match_id:
        query = query.filter(Event.match_id == match_id)

    if event_type:
        query = query.filter(Event.event_type_name == event_type)

    if limit:
        query = query.limit(limit)

    return query.all()
