"""
CRUD operations for PlayerSeasonStatistics model.

Functions:
- get_or_create_player_season_statistics: Get existing or create new player season stats
- update_player_season_statistics: Update player season statistics
- recalculate_player_season_statistics: Recalculate from all player match statistics
- calculate_player_attributes: Calculate 5 attribute ratings (0-100) from stats
"""

from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.player_season_statistics import PlayerSeasonStatistics
from app.models.player_match_statistics import PlayerMatchStatistics


def get_or_create_player_season_statistics(
    db: Session,
    player_id: str
) -> PlayerSeasonStatistics:
    """
    Get existing player season statistics or create if not exists.

    Args:
        db: Database session
        player_id: Player UUID

    Returns:
        PlayerSeasonStatistics instance

    Example:
        >>> stats = get_or_create_player_season_statistics(db, "550e8400-...")
        >>> print(f"Goals: {stats.goals}, Assists: {stats.assists}")
    """
    # Try to find existing statistics
    player_stats = db.query(PlayerSeasonStatistics).filter(
        PlayerSeasonStatistics.player_id == player_id
    ).first()

    if player_stats:
        return player_stats

    # Create new record with default values
    player_stats = PlayerSeasonStatistics(
        player_id=player_id,
        matches_played=0,
        goals=0,
        assists=0,
        updated_at=datetime.now(timezone.utc)
    )

    db.add(player_stats)
    db.flush()
    db.refresh(player_stats)

    return player_stats


def update_player_season_statistics(
    db: Session,
    player_id: str,
    **stats_data
) -> PlayerSeasonStatistics:
    """
    Update player season statistics.

    Args:
        db: Database session
        player_id: Player UUID
        **stats_data: Statistics fields as keyword arguments

    Returns:
        Updated PlayerSeasonStatistics instance

    Example:
        >>> stats = update_player_season_statistics(
        ...     db,
        ...     player_id="550e8400-...",
        ...     goals=15,
        ...     assists=8,
        ...     attacking_rating=85
        ... )
    """
    player_stats = get_or_create_player_season_statistics(db, player_id)

    # Update fields
    for field, value in stats_data.items():
        if hasattr(player_stats, field):
            setattr(player_stats, field, value)

    player_stats.updated_at = datetime.now(timezone.utc)

    db.flush()
    db.refresh(player_stats)

    return player_stats


def calculate_player_attributes(
    goals: int,
    assists: int,
    shots_per_game: Optional[float],
    total_passes: int,
    passes_completed: int,
    total_dribbles: int,
    successful_dribbles: int,
    tackles: int,
    tackle_success_rate: Optional[float],
    interceptions: int
) -> dict:
    """
    Calculate player attribute ratings (0-100) from statistics.

    This is a simplified calculation. In production, you'd want more
    sophisticated algorithms based on position, league averages, etc.

    The 5 attributes are:
    - attacking_rating: Goals, assists, shots
    - technique_rating: Dribble success, pass completion
    - tactical_rating: Positioning, pass types, decision making
    - defending_rating: Tackles, interceptions
    - creativity_rating: Assists, final third passes, key passes

    Args:
        [Various statistics parameters]

    Returns:
        Dictionary with 5 attribute ratings (0-100)

    Example:
        >>> attrs = calculate_player_attributes(
        ...     goals=10, assists=5, shots_per_game=3.5,
        ...     total_passes=500, passes_completed=425,
        ...     total_dribbles=50, successful_dribbles=35,
        ...     tackles=30, tackle_success_rate=70.0,
        ...     interceptions=25
        ... )
        >>> print(f"Attacking: {attrs['attacking_rating']}")
    """
    # Attacking rating (0-100)
    # Based on goals, assists, and shots
    attacking_score = min(100, (goals * 5) + (assists * 3) + (shots_per_game or 0) * 2)

    # Technique rating (0-100)
    # Based on dribble success and pass completion
    pass_accuracy = (passes_completed / total_passes * 100) if total_passes > 0 else 0
    dribble_success = (successful_dribbles / total_dribbles * 100) if total_dribbles > 0 else 0
    technique_score = min(100, (pass_accuracy * 0.6) + (dribble_success * 0.4))

    # Tactical rating (0-100)
    # Based on overall involvement and decision making
    # This is simplified - would need more sophisticated metrics
    tactical_score = min(100, pass_accuracy * 0.7 + (successful_dribbles / (total_dribbles or 1)) * 30)

    # Defending rating (0-100)
    # Based on tackles and interceptions
    tackle_contribution = (tackles * 2) + (tackle_success_rate or 0) * 0.3
    interception_contribution = interceptions * 2
    defending_score = min(100, tackle_contribution + interception_contribution)

    # Creativity rating (0-100)
    # Based on assists and passing
    creativity_score = min(100, (assists * 8) + (pass_accuracy * 0.3))

    return {
        "attacking_rating": int(round(attacking_score)),
        "technique_rating": int(round(technique_score)),
        "tactical_rating": int(round(tactical_score)),
        "defending_rating": int(round(defending_score)),
        "creativity_rating": int(round(creativity_score))
    }


def recalculate_player_season_statistics(
    db: Session,
    player_id: str
) -> PlayerSeasonStatistics:
    """
    Recalculate player season statistics from all player match statistics.

    This aggregates data from player_match_statistics table and calculates
    the 5 player attributes (0-100 ratings).

    Should be called after each match upload to update season totals.

    Args:
        db: Database session
        player_id: Player UUID

    Returns:
        Recalculated PlayerSeasonStatistics instance

    Example:
        >>> stats = recalculate_player_season_statistics(db, "550e8400-...")
        >>> print(f"Season: {stats.goals}G {stats.assists}A, Attack:{stats.attacking_rating}")
    """
    player_stats = get_or_create_player_season_statistics(db, player_id)

    # Get all match statistics for this player
    match_stats = db.query(PlayerMatchStatistics).filter(
        PlayerMatchStatistics.player_id == player_id
    ).all()

    if not match_stats:
        # No match data yet - return default stats
        return player_stats

    matches_played = len(match_stats)

    # Aggregate totals
    total_goals = sum(s.goals for s in match_stats)
    total_assists = sum(s.assists for s in match_stats)
    total_xg = sum(float(s.expected_goals or 0) for s in match_stats)

    total_shots = sum(s.shots or 0 for s in match_stats)
    total_shots_on_target = sum(s.shots_on_target or 0 for s in match_stats)

    total_passes = sum(s.total_passes or 0 for s in match_stats)
    completed_passes = sum(s.completed_passes or 0 for s in match_stats)

    total_dribbles = sum(s.total_dribbles or 0 for s in match_stats)
    successful_dribbles = sum(s.successful_dribbles or 0 for s in match_stats)

    total_tackles = sum(s.tackles or 0 for s in match_stats)
    # Calculate average tackle success rate
    tackle_rates = [float(s.tackle_success_rate or 0) for s in match_stats if s.tackle_success_rate]
    avg_tackle_success = sum(tackle_rates) / len(tackle_rates) if tackle_rates else None

    total_interceptions = sum(s.interceptions or 0 for s in match_stats)
    # Calculate average interception success rate
    interception_rates = [float(s.interception_success_rate or 0) for s in match_stats if s.interception_success_rate]
    avg_interception_success = sum(interception_rates) / len(interception_rates) if interception_rates else None

    # Calculate per-game averages
    shots_per_game = total_shots / matches_played if matches_played > 0 else None
    shots_on_target_per_game = total_shots_on_target / matches_played if matches_played > 0 else None

    # Calculate player attributes (0-100 ratings)
    attributes = calculate_player_attributes(
        goals=total_goals,
        assists=total_assists,
        shots_per_game=shots_per_game,
        total_passes=total_passes,
        passes_completed=completed_passes,
        total_dribbles=total_dribbles,
        successful_dribbles=successful_dribbles,
        tackles=total_tackles,
        tackle_success_rate=avg_tackle_success,
        interceptions=total_interceptions
    )

    # Update player season statistics
    player_stats.matches_played = matches_played
    player_stats.goals = total_goals
    player_stats.assists = total_assists
    player_stats.expected_goals = Decimal(str(round(total_xg, 6))) if total_xg > 0 else None
    player_stats.shots_per_game = Decimal(str(round(shots_per_game, 2))) if shots_per_game else None
    player_stats.shots_on_target_per_game = Decimal(str(round(shots_on_target_per_game, 2))) if shots_on_target_per_game else None
    player_stats.total_passes = total_passes if total_passes > 0 else None
    player_stats.passes_completed = completed_passes if completed_passes > 0 else None
    player_stats.total_dribbles = total_dribbles if total_dribbles > 0 else None
    player_stats.successful_dribbles = successful_dribbles if successful_dribbles > 0 else None
    player_stats.tackles = total_tackles if total_tackles > 0 else None
    player_stats.tackle_success_rate = Decimal(str(round(avg_tackle_success, 2))) if avg_tackle_success else None
    player_stats.interceptions = total_interceptions if total_interceptions > 0 else None
    player_stats.interception_success_rate = Decimal(str(round(avg_interception_success, 2))) if avg_interception_success else None

    # Set attribute ratings
    player_stats.attacking_rating = attributes["attacking_rating"]
    player_stats.technique_rating = attributes["technique_rating"]
    player_stats.tactical_rating = attributes["tactical_rating"]
    player_stats.defending_rating = attributes["defending_rating"]
    player_stats.creativity_rating = attributes["creativity_rating"]

    player_stats.updated_at = datetime.now(timezone.utc)

    db.flush()
    db.refresh(player_stats)

    return player_stats
