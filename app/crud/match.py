"""
CRUD operations for Match model.

Functions:
- create_match: Create new match record
- get_match_by_id: Get match by ID
- get_matches_by_club: Get all matches for a club
- update_match_scores: Update match final scores
"""

from typing import Optional, List
from datetime import date, time, datetime, timezone

from sqlalchemy.orm import Session

from app.models.match import Match


def create_match(
    db: Session,
    club_id: str,
    opponent_name: str,
    match_date: date,
    is_home_match: bool,
    opponent_club_id: Optional[str] = None,
    match_time: Optional[time] = None,
    home_score: Optional[int] = None,
    away_score: Optional[int] = None
) -> Match:
    """
    Create a new match record.

    Args:
        db: Database session
        club_id: UUID of our club
        opponent_name: Name of opponent team
        match_date: Date of the match
        is_home_match: True if home match, False if away
        opponent_club_id: Optional UUID of opponent club (if exists in opponent_clubs)
        match_time: Optional match time
        home_score: Optional home team score
        away_score: Optional away team score

    Returns:
        Created Match instance

    Example:
        >>> match = create_match(
        ...     db,
        ...     club_id="550e8400-e29b-41d4-a716-446655440000",
        ...     opponent_name="Barcelona",
        ...     match_date=date(2024, 3, 15),
        ...     is_home_match=True,
        ...     home_score=2,
        ...     away_score=1
        ... )
    """
    now = datetime.now(timezone.utc)

    match = Match(
        club_id=club_id,
        opponent_club_id=opponent_club_id,
        opponent_name=opponent_name,
        match_date=match_date,
        match_time=match_time,
        is_home_match=is_home_match,
        home_score=home_score,
        away_score=away_score,
        created_at=now,
        updated_at=now
    )

    db.add(match)
    db.flush()
    db.refresh(match)

    return match


def get_match_by_id(db: Session, match_id: str) -> Optional[Match]:
    """
    Retrieve a match by match_id.

    Args:
        db: Database session
        match_id: Match UUID

    Returns:
        Match instance if found, None otherwise

    Example:
        >>> match = get_match_by_id(db, "550e8400-e29b-41d4-a716-446655440000")
        >>> if match:
        ...     print(f"{match.opponent_name}: {match.home_score}-{match.away_score}")
    """
    return db.query(Match).filter(Match.match_id == match_id).first()


def get_matches_by_club(
    db: Session,
    club_id: str,
    limit: Optional[int] = None
) -> List[Match]:
    """
    Get all matches for a specific club.

    Args:
        db: Database session
        club_id: Club UUID
        limit: Optional limit on number of results

    Returns:
        List of Match instances ordered by date (most recent first)

    Example:
        >>> matches = get_matches_by_club(db, club_id="550e8400-...", limit=10)
        >>> for match in matches:
        ...     print(f"{match.match_date}: {match.opponent_name}")
    """
    query = db.query(Match).filter(Match.club_id == club_id).order_by(Match.match_date.desc())

    if limit:
        query = query.limit(limit)

    return query.all()


def update_match_scores(
    db: Session,
    match_id: str,
    home_score: int,
    away_score: int
) -> Match:
    """
    Update match final scores.

    Args:
        db: Database session
        match_id: Match UUID
        home_score: Final home team score
        away_score: Final away team score

    Returns:
        Updated Match instance

    Raises:
        ValueError: If match not found

    Example:
        >>> match = update_match_scores(
        ...     db,
        ...     match_id="550e8400-...",
        ...     home_score=3,
        ...     away_score=2
        ... )
    """
    match = get_match_by_id(db, match_id)

    if not match:
        raise ValueError(f"Match not found: {match_id}")

    match.home_score = home_score
    match.away_score = away_score
    match.updated_at = datetime.now(timezone.utc)

    db.flush()
    db.refresh(match)

    return match
