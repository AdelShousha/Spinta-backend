"""
CRUD operations for Club model.

Functions:
- create_club: Create new club
- get_club_by_id: Get club by ID
- get_club_by_coach: Get club by coach ID
- update_club: Update club information
"""

from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.club import Club


def create_club(
    db: Session,
    coach_id: str,
    club_name: str,
    country: Optional[str] = None,
    age_group: Optional[str] = None,
    stadium: Optional[str] = None,
    logo_url: Optional[str] = None,
    statsbomb_team_id: Optional[int] = None
) -> Club:
    """
    Create a new club.

    Args:
        db: Database session
        coach_id: UUID of the coach who owns the club
        club_name: Name of the club
        country: Optional country
        age_group: Optional age group (e.g., 'U16', 'U18')
        stadium: Optional stadium name
        logo_url: Optional club logo URL
        statsbomb_team_id: Optional StatsBomb team ID

    Returns:
        Created Club instance

    Example:
        >>> club = create_club(
        ...     db,
        ...     coach_id="550e8400-...",
        ...     club_name="Thunder United FC",
        ...     country="United States",
        ...     age_group="U16",
        ...     stadium="Thunder Stadium"
        ... )
    """
    now = datetime.now(timezone.utc)

    club = Club(
        coach_id=coach_id,
        club_name=club_name,
        country=country,
        age_group=age_group,
        stadium=stadium,
        logo_url=logo_url,
        statsbomb_team_id=statsbomb_team_id,
        created_at=now,
        updated_at=now
    )

    db.add(club)
    db.flush()
    db.refresh(club)

    return club


def get_club_by_id(db: Session, club_id: str) -> Optional[Club]:
    """
    Retrieve a club by club_id.

    Args:
        db: Database session
        club_id: Club UUID

    Returns:
        Club instance if found, None otherwise

    Example:
        >>> club = get_club_by_id(db, "550e8400-...")
        >>> if club:
        ...     print(f"{club.club_name} - {club.age_group}")
    """
    return db.query(Club).filter(Club.club_id == club_id).first()


def get_club_by_coach(db: Session, coach_id: str) -> Optional[Club]:
    """
    Retrieve a club by coach_id (one-to-one relationship).

    Args:
        db: Database session
        coach_id: Coach UUID

    Returns:
        Club instance if found, None otherwise

    Example:
        >>> club = get_club_by_coach(db, "660e8400-...")
        >>> if club:
        ...     print(f"Coach's club: {club.club_name}")
    """
    return db.query(Club).filter(Club.coach_id == coach_id).first()


def update_club(
    db: Session,
    club_id: str,
    **club_data
) -> Club:
    """
    Update club information.

    Args:
        db: Database session
        club_id: Club UUID
        **club_data: Club fields as keyword arguments

    Returns:
        Updated Club instance

    Raises:
        ValueError: If club not found

    Example:
        >>> club = update_club(
        ...     db,
        ...     club_id="550e8400-...",
        ...     club_name="Thunder United FC Elite",
        ...     stadium="New Thunder Stadium",
        ...     logo_url="https://example.com/new_logo.png"
        ... )
    """
    club = get_club_by_id(db, club_id)

    if not club:
        raise ValueError(f"Club not found: {club_id}")

    # Update fields
    for field, value in club_data.items():
        if hasattr(club, field) and field not in ['club_id', 'coach_id', 'created_at']:
            setattr(club, field, value)

    club.updated_at = datetime.now(timezone.utc)

    db.flush()
    db.refresh(club)

    return club
