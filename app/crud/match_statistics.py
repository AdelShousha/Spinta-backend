"""
CRUD operations for MatchStatistics model.

Functions:
- create_match_statistics: Create match statistics record
- get_match_statistics_by_match: Get statistics for a match (both teams)
- upsert_match_statistics: Create or update match statistics
"""

from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.match_statistics import MatchStatistics


def create_match_statistics(
    db: Session,
    match_id: str,
    team_type: str,
    possession_percentage: Optional[Decimal] = None,
    expected_goals: Optional[Decimal] = None,
    total_shots: Optional[int] = None,
    shots_on_target: Optional[int] = None,
    shots_off_target: Optional[int] = None,
    goalkeeper_saves: Optional[int] = None,
    total_passes: Optional[int] = None,
    passes_completed: Optional[int] = None,
    pass_completion_rate: Optional[Decimal] = None,
    passes_in_final_third: Optional[int] = None,
    long_passes: Optional[int] = None,
    crosses: Optional[int] = None,
    total_dribbles: Optional[int] = None,
    successful_dribbles: Optional[int] = None,
    total_tackles: Optional[int] = None,
    tackle_success_percentage: Optional[Decimal] = None,
    interceptions: Optional[int] = None,
    ball_recoveries: Optional[int] = None
) -> MatchStatistics:
    """
    Create a new match statistics record.

    Args:
        db: Database session
        match_id: UUID of the match
        team_type: 'our_team' or 'opponent_team'
        [All other statistics fields are optional]

    Returns:
        Created MatchStatistics instance

    Example:
        >>> stats = create_match_statistics(
        ...     db,
        ...     match_id="550e8400-...",
        ...     team_type="our_team",
        ...     possession_percentage=Decimal("58.5"),
        ...     total_shots=15,
        ...     shots_on_target=8
        ... )
    """
    match_stats = MatchStatistics(
        match_id=match_id,
        team_type=team_type,
        possession_percentage=possession_percentage,
        expected_goals=expected_goals,
        total_shots=total_shots,
        shots_on_target=shots_on_target,
        shots_off_target=shots_off_target,
        goalkeeper_saves=goalkeeper_saves,
        total_passes=total_passes,
        passes_completed=passes_completed,
        pass_completion_rate=pass_completion_rate,
        passes_in_final_third=passes_in_final_third,
        long_passes=long_passes,
        crosses=crosses,
        total_dribbles=total_dribbles,
        successful_dribbles=successful_dribbles,
        total_tackles=total_tackles,
        tackle_success_percentage=tackle_success_percentage,
        interceptions=interceptions,
        ball_recoveries=ball_recoveries,
        created_at=datetime.now(timezone.utc)
    )

    db.add(match_stats)
    db.flush()
    db.refresh(match_stats)

    return match_stats


def get_match_statistics_by_match(
    db: Session,
    match_id: str,
    team_type: Optional[str] = None
) -> List[MatchStatistics]:
    """
    Get match statistics for a specific match.

    Args:
        db: Database session
        match_id: Match UUID
        team_type: Optional filter for 'our_team' or 'opponent_team'

    Returns:
        List of MatchStatistics instances (2 per match if no team_type filter)

    Example:
        >>> all_stats = get_match_statistics_by_match(db, "550e8400-...")
        >>> our_stats = get_match_statistics_by_match(db, "550e8400-...", "our_team")
    """
    query = db.query(MatchStatistics).filter(MatchStatistics.match_id == match_id)

    if team_type:
        query = query.filter(MatchStatistics.team_type == team_type)

    return query.all()


def upsert_match_statistics(
    db: Session,
    match_id: str,
    team_type: str,
    **stats_data
) -> MatchStatistics:
    """
    Create or update match statistics (upsert operation).

    This checks if statistics already exist for the match+team combination.
    If they exist, updates them. If not, creates new record.

    Args:
        db: Database session
        match_id: Match UUID
        team_type: 'our_team' or 'opponent_team'
        **stats_data: All statistics fields as keyword arguments

    Returns:
        MatchStatistics instance (existing updated or newly created)

    Example:
        >>> stats = upsert_match_statistics(
        ...     db,
        ...     match_id="550e8400-...",
        ...     team_type="our_team",
        ...     possession_percentage=Decimal("60.0"),
        ...     total_shots=20
        ... )
    """
    # Try to find existing statistics
    existing_stats = db.query(MatchStatistics).filter(
        MatchStatistics.match_id == match_id,
        MatchStatistics.team_type == team_type
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
        return create_match_statistics(
            db=db,
            match_id=match_id,
            team_type=team_type,
            **stats_data
        )
