"""
CRUD operations for PlayerMatchStatistics model.

Functions:
- create_player_match_statistics: Create player match statistics record
- get_player_match_statistics_by_player: Get all match stats for a player
- get_player_match_statistics_by_match: Get all player stats for a match
- upsert_player_match_statistics: Create or update player match statistics
"""

from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.player_match_statistics import PlayerMatchStatistics


def create_player_match_statistics(
    db: Session,
    player_id: str,
    match_id: str,
    goals: int = 0,
    assists: int = 0,
    expected_goals: Optional[Decimal] = None,
    shots: Optional[int] = None,
    shots_on_target: Optional[int] = None,
    total_dribbles: Optional[int] = None,
    successful_dribbles: Optional[int] = None,
    total_passes: Optional[int] = None,
    completed_passes: Optional[int] = None,
    short_passes: Optional[int] = None,
    long_passes: Optional[int] = None,
    final_third_passes: Optional[int] = None,
    crosses: Optional[int] = None,
    tackles: Optional[int] = None,
    tackle_success_rate: Optional[Decimal] = None,
    interceptions: Optional[int] = None,
    interception_success_rate: Optional[Decimal] = None
) -> PlayerMatchStatistics:
    """
    Create a new player match statistics record.

    Args:
        db: Database session
        player_id: UUID of the player
        match_id: UUID of the match
        goals: Goals scored (default 0)
        assists: Assists made (default 0)
        [All other statistics fields are optional]

    Returns:
        Created PlayerMatchStatistics instance

    Example:
        >>> stats = create_player_match_statistics(
        ...     db,
        ...     player_id="550e8400-...",
        ...     match_id="660e8400-...",
        ...     goals=2,
        ...     assists=1,
        ...     shots=5,
        ...     shots_on_target=3
        ... )
    """
    player_stats = PlayerMatchStatistics(
        player_id=player_id,
        match_id=match_id,
        goals=goals,
        assists=assists,
        expected_goals=expected_goals,
        shots=shots,
        shots_on_target=shots_on_target,
        total_dribbles=total_dribbles,
        successful_dribbles=successful_dribbles,
        total_passes=total_passes,
        completed_passes=completed_passes,
        short_passes=short_passes,
        long_passes=long_passes,
        final_third_passes=final_third_passes,
        crosses=crosses,
        tackles=tackles,
        tackle_success_rate=tackle_success_rate,
        interceptions=interceptions,
        interception_success_rate=interception_success_rate,
        created_at=datetime.now(timezone.utc)
    )

    db.add(player_stats)
    db.flush()
    db.refresh(player_stats)

    return player_stats


def get_player_match_statistics_by_player(
    db: Session,
    player_id: str,
    limit: Optional[int] = None
) -> List[PlayerMatchStatistics]:
    """
    Get all match statistics for a specific player.

    Args:
        db: Database session
        player_id: Player UUID
        limit: Optional limit on number of results

    Returns:
        List of PlayerMatchStatistics instances ordered by created_at desc

    Example:
        >>> stats = get_player_match_statistics_by_player(db, "550e8400-...", limit=10)
        >>> for stat in stats:
        ...     print(f"Match: {stat.match_id}, Goals: {stat.goals}")
    """
    query = db.query(PlayerMatchStatistics).filter(
        PlayerMatchStatistics.player_id == player_id
    ).order_by(PlayerMatchStatistics.created_at.desc())

    if limit:
        query = query.limit(limit)

    return query.all()


def get_player_match_statistics_by_match(
    db: Session,
    match_id: str
) -> List[PlayerMatchStatistics]:
    """
    Get all player statistics for a specific match.

    Args:
        db: Database session
        match_id: Match UUID

    Returns:
        List of PlayerMatchStatistics instances for all players in that match

    Example:
        >>> stats = get_player_match_statistics_by_match(db, "660e8400-...")
        >>> for stat in stats:
        ...     print(f"Player: {stat.player_id}, Goals: {stat.goals}")
    """
    return db.query(PlayerMatchStatistics).filter(
        PlayerMatchStatistics.match_id == match_id
    ).all()


def upsert_player_match_statistics(
    db: Session,
    player_id: str,
    match_id: str,
    **stats_data
) -> PlayerMatchStatistics:
    """
    Create or update player match statistics (upsert operation).

    This checks if statistics already exist for the player+match combination.
    If they exist, updates them. If not, creates new record.

    Args:
        db: Database session
        player_id: Player UUID
        match_id: Match UUID
        **stats_data: All statistics fields as keyword arguments

    Returns:
        PlayerMatchStatistics instance (existing updated or newly created)

    Example:
        >>> stats = upsert_player_match_statistics(
        ...     db,
        ...     player_id="550e8400-...",
        ...     match_id="660e8400-...",
        ...     goals=3,
        ...     assists=2,
        ...     shots=7
        ... )
    """
    # Try to find existing statistics
    existing_stats = db.query(PlayerMatchStatistics).filter(
        PlayerMatchStatistics.player_id == player_id,
        PlayerMatchStatistics.match_id == match_id
    ).first()

    if existing_stats:
        # Update existing record
        for field, value in stats_data.items():
            if hasattr(existing_stats, field):
                setattr(existing_stats, field, value)

        db.flush()
        db.refresh(existing_stats)
        return existing_stats
    else:
        # Create new record
        return create_player_match_statistics(
            db=db,
            player_id=player_id,
            match_id=match_id,
            **stats_data
        )
