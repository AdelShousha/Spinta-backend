"""
CRUD operations for OpponentPlayer model.

Functions:
- get_opponent_player_by_statsbomb_id: Find opponent player by StatsBomb player ID
- create_opponent_player: Create new opponent player
- get_or_create_opponent_player: Get existing or create new opponent player
"""

from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.opponent_player import OpponentPlayer


def get_opponent_player_by_statsbomb_id(
    db: Session,
    statsbomb_player_id: int
) -> Optional[OpponentPlayer]:
    """
    Retrieve an opponent player by StatsBomb player ID.

    Args:
        db: Database session
        statsbomb_player_id: StatsBomb player ID

    Returns:
        OpponentPlayer instance if found, None otherwise

    Example:
        >>> player = get_opponent_player_by_statsbomb_id(db, 789)
        >>> if player:
        ...     print(player.player_name)
    """
    return db.query(OpponentPlayer).filter(
        OpponentPlayer.statsbomb_player_id == statsbomb_player_id
    ).first()


def create_opponent_player(
    db: Session,
    opponent_club_id: str,
    player_name: str,
    statsbomb_player_id: Optional[int] = None,
    jersey_number: Optional[int] = None,
    position: Optional[str] = None
) -> OpponentPlayer:
    """
    Create a new opponent player record.

    Args:
        db: Database session
        opponent_club_id: UUID of the opponent club
        player_name: Name of the player
        statsbomb_player_id: Optional StatsBomb player ID
        jersey_number: Optional jersey number
        position: Optional player position

    Returns:
        Created OpponentPlayer instance

    Example:
        >>> player = create_opponent_player(
        ...     db,
        ...     opponent_club_id="550e8400-e29b-41d4-a716-446655440000",
        ...     player_name="Lionel Messi",
        ...     statsbomb_player_id=789,
        ...     jersey_number=10,
        ...     position="Forward"
        ... )
    """
    opponent_player = OpponentPlayer(
        opponent_club_id=opponent_club_id,
        player_name=player_name,
        statsbomb_player_id=statsbomb_player_id,
        jersey_number=jersey_number,
        position=position,
        created_at=datetime.now(timezone.utc)
    )

    db.add(opponent_player)
    db.flush()
    db.refresh(opponent_player)

    return opponent_player


def get_or_create_opponent_player(
    db: Session,
    opponent_club_id: str,
    player_name: str,
    statsbomb_player_id: Optional[int] = None,
    jersey_number: Optional[int] = None,
    position: Optional[str] = None
) -> OpponentPlayer:
    """
    Get existing opponent player or create if not exists.

    This is useful for match upload where we might encounter
    the same opponent player multiple times.

    Args:
        db: Database session
        opponent_club_id: UUID of the opponent club
        player_name: Name of the player
        statsbomb_player_id: Optional StatsBomb player ID
        jersey_number: Optional jersey number
        position: Optional player position

    Returns:
        OpponentPlayer instance (existing or newly created)

    Example:
        >>> player = get_or_create_opponent_player(
        ...     db,
        ...     opponent_club_id="550e8400-e29b-41d4-a716-446655440000",
        ...     player_name="Cristiano Ronaldo",
        ...     statsbomb_player_id=456,
        ...     jersey_number=7
        ... )
    """
    # Try to find by StatsBomb ID first (more reliable)
    if statsbomb_player_id:
        opponent_player = get_opponent_player_by_statsbomb_id(db, statsbomb_player_id)
        if opponent_player:
            return opponent_player

    # Try to find by club and name
    opponent_player = db.query(OpponentPlayer).filter(
        OpponentPlayer.opponent_club_id == opponent_club_id,
        OpponentPlayer.player_name == player_name
    ).first()

    if opponent_player:
        return opponent_player

    # Create new opponent player
    return create_opponent_player(
        db=db,
        opponent_club_id=opponent_club_id,
        player_name=player_name,
        statsbomb_player_id=statsbomb_player_id,
        jersey_number=jersey_number,
        position=position
    )
