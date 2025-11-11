"""
CRUD operations for OpponentClub model.

Functions:
- get_opponent_club_by_statsbomb_id: Find opponent club by StatsBomb team ID
- create_opponent_club: Create new opponent club
- get_or_create_opponent_club: Get existing or create new opponent club
"""

from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.opponent_club import OpponentClub


def get_opponent_club_by_statsbomb_id(
    db: Session,
    statsbomb_team_id: int
) -> Optional[OpponentClub]:
    """
    Retrieve an opponent club by StatsBomb team ID.

    Args:
        db: Database session
        statsbomb_team_id: StatsBomb team ID

    Returns:
        OpponentClub instance if found, None otherwise

    Example:
        >>> club = get_opponent_club_by_statsbomb_id(db, 456)
        >>> if club:
        ...     print(club.opponent_name)
    """
    return db.query(OpponentClub).filter(
        OpponentClub.statsbomb_team_id == statsbomb_team_id
    ).first()


def create_opponent_club(
    db: Session,
    opponent_name: str,
    statsbomb_team_id: Optional[int] = None,
    logo_url: Optional[str] = None
) -> OpponentClub:
    """
    Create a new opponent club record.

    Args:
        db: Database session
        opponent_name: Name of the opponent club
        statsbomb_team_id: Optional StatsBomb team ID
        logo_url: Optional club logo URL

    Returns:
        Created OpponentClub instance

    Example:
        >>> club = create_opponent_club(
        ...     db,
        ...     opponent_name="Real Madrid",
        ...     statsbomb_team_id=456,
        ...     logo_url="https://example.com/logo.png"
        ... )
    """
    opponent_club = OpponentClub(
        opponent_name=opponent_name,
        statsbomb_team_id=statsbomb_team_id,
        logo_url=logo_url,
        created_at=datetime.now(timezone.utc)
    )

    db.add(opponent_club)
    db.flush()
    db.refresh(opponent_club)

    return opponent_club


def get_or_create_opponent_club(
    db: Session,
    opponent_name: str,
    statsbomb_team_id: Optional[int] = None,
    logo_url: Optional[str] = None
) -> OpponentClub:
    """
    Get existing opponent club or create if not exists.

    This is useful for match upload where we might encounter
    the same opponent multiple times.

    Args:
        db: Database session
        opponent_name: Name of the opponent club
        statsbomb_team_id: Optional StatsBomb team ID
        logo_url: Optional club logo URL

    Returns:
        OpponentClub instance (existing or newly created)

    Example:
        >>> club = get_or_create_opponent_club(
        ...     db,
        ...     opponent_name="Barcelona",
        ...     statsbomb_team_id=789
        ... )
    """
    # Try to find by StatsBomb ID first (more reliable)
    if statsbomb_team_id:
        opponent_club = get_opponent_club_by_statsbomb_id(db, statsbomb_team_id)
        if opponent_club:
            return opponent_club

    # Try to find by name
    opponent_club = db.query(OpponentClub).filter(
        OpponentClub.opponent_name == opponent_name
    ).first()

    if opponent_club:
        return opponent_club

    # Create new opponent club
    return create_opponent_club(
        db=db,
        opponent_name=opponent_name,
        statsbomb_team_id=statsbomb_team_id,
        logo_url=logo_url
    )
