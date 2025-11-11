"""
CRUD operations for ClubSeasonStatistics model.

Functions:
- get_or_create_club_season_statistics: Get existing or create new club season stats
- update_club_season_statistics: Update club season statistics
- recalculate_club_season_statistics: Recalculate from all matches and match statistics
"""

from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.club_season_statistics import ClubSeasonStatistics
from app.models.match import Match
from app.models.match_statistics import MatchStatistics


def get_or_create_club_season_statistics(
    db: Session,
    club_id: str
) -> ClubSeasonStatistics:
    """
    Get existing club season statistics or create if not exists.

    Args:
        db: Database session
        club_id: Club UUID

    Returns:
        ClubSeasonStatistics instance

    Example:
        >>> stats = get_or_create_club_season_statistics(db, "550e8400-...")
        >>> print(f"Matches played: {stats.matches_played}")
    """
    # Try to find existing statistics
    club_stats = db.query(ClubSeasonStatistics).filter(
        ClubSeasonStatistics.club_id == club_id
    ).first()

    if club_stats:
        return club_stats

    # Create new record with default values
    club_stats = ClubSeasonStatistics(
        club_id=club_id,
        matches_played=0,
        wins=0,
        draws=0,
        losses=0,
        goals_scored=0,
        goals_conceded=0,
        total_clean_sheets=0,
        updated_at=datetime.now(timezone.utc)
    )

    db.add(club_stats)
    db.flush()
    db.refresh(club_stats)

    return club_stats


def update_club_season_statistics(
    db: Session,
    club_id: str,
    **stats_data
) -> ClubSeasonStatistics:
    """
    Update club season statistics.

    Args:
        db: Database session
        club_id: Club UUID
        **stats_data: Statistics fields as keyword arguments

    Returns:
        Updated ClubSeasonStatistics instance

    Example:
        >>> stats = update_club_season_statistics(
        ...     db,
        ...     club_id="550e8400-...",
        ...     matches_played=10,
        ...     wins=6,
        ...     draws=2,
        ...     losses=2
        ... )
    """
    club_stats = get_or_create_club_season_statistics(db, club_id)

    # Update fields
    for field, value in stats_data.items():
        if hasattr(club_stats, field):
            setattr(club_stats, field, value)

    club_stats.updated_at = datetime.now(timezone.utc)

    db.flush()
    db.refresh(club_stats)

    return club_stats


def recalculate_club_season_statistics(
    db: Session,
    club_id: str
) -> ClubSeasonStatistics:
    """
    Recalculate club season statistics from all matches and match statistics.

    This aggregates data from:
    - matches table (wins/draws/losses, goals scored/conceded)
    - match_statistics table (possession, xG, passes, shots, etc.)

    Should be called after each match upload to update season totals.

    Args:
        db: Database session
        club_id: Club UUID

    Returns:
        Recalculated ClubSeasonStatistics instance

    Example:
        >>> stats = recalculate_club_season_statistics(db, "550e8400-...")
        >>> print(f"Updated season stats: {stats.wins}W {stats.draws}D {stats.losses}L")
    """
    club_stats = get_or_create_club_season_statistics(db, club_id)

    # Get all matches for this club
    matches = db.query(Match).filter(Match.club_id == club_id).all()

    # Calculate match results
    matches_played = len(matches)
    wins = 0
    draws = 0
    losses = 0
    goals_scored = 0
    goals_conceded = 0
    clean_sheets = 0

    for match in matches:
        if match.home_score is not None and match.away_score is not None:
            if match.is_home_match:
                our_score = match.home_score
                their_score = match.away_score
            else:
                our_score = match.away_score
                their_score = match.home_score

            goals_scored += our_score
            goals_conceded += their_score

            if their_score == 0:
                clean_sheets += 1

            if our_score > their_score:
                wins += 1
            elif our_score == their_score:
                draws += 1
            else:
                losses += 1

    # Get aggregated match statistics for our team
    match_stats = db.query(MatchStatistics).filter(
        MatchStatistics.match_id.in_([m.match_id for m in matches]),
        MatchStatistics.team_type == "our_team"
    ).all()

    # Calculate averages from match statistics
    if match_stats:
        stats_count = len(match_stats)

        avg_possession = sum(
            float(s.possession_percentage or 0) for s in match_stats
        ) / stats_count if stats_count > 0 else None

        avg_xg = sum(
            float(s.expected_goals or 0) for s in match_stats
        ) / stats_count if stats_count > 0 else None

        avg_shots = sum(
            s.total_shots or 0 for s in match_stats
        ) / stats_count if stats_count > 0 else None

        avg_shots_on_target = sum(
            s.shots_on_target or 0 for s in match_stats
        ) / stats_count if stats_count > 0 else None

        avg_passes = sum(
            s.total_passes or 0 for s in match_stats
        ) / stats_count if stats_count > 0 else None

        # Calculate overall pass completion rate
        total_passes = sum(s.total_passes or 0 for s in match_stats)
        completed_passes = sum(s.passes_completed or 0 for s in match_stats)
        pass_completion = (completed_passes / total_passes * 100) if total_passes > 0 else None

        avg_final_third = sum(
            s.passes_in_final_third or 0 for s in match_stats
        ) / stats_count if stats_count > 0 else None

        avg_crosses = sum(
            s.crosses or 0 for s in match_stats
        ) / stats_count if stats_count > 0 else None

        avg_dribbles = sum(
            s.total_dribbles or 0 for s in match_stats
        ) / stats_count if stats_count > 0 else None

        avg_successful_dribbles = sum(
            s.successful_dribbles or 0 for s in match_stats
        ) / stats_count if stats_count > 0 else None

        avg_tackles = sum(
            s.total_tackles or 0 for s in match_stats
        ) / stats_count if stats_count > 0 else None

        # Calculate overall tackle success rate
        total_tackles = sum(s.total_tackles or 0 for s in match_stats)
        # For tackle success, we need to derive from percentages if available
        tackle_success = avg_possession  # Placeholder - would need proper calculation

        avg_interceptions = sum(
            s.interceptions or 0 for s in match_stats
        ) / stats_count if stats_count > 0 else None

        avg_ball_recoveries = sum(
            s.ball_recoveries or 0 for s in match_stats
        ) / stats_count if stats_count > 0 else None

        avg_saves = sum(
            s.goalkeeper_saves or 0 for s in match_stats
        ) / stats_count if stats_count > 0 else None
    else:
        avg_possession = avg_xg = avg_shots = avg_shots_on_target = None
        avg_passes = pass_completion = avg_final_third = avg_crosses = None
        avg_dribbles = avg_successful_dribbles = avg_tackles = None
        tackle_success = avg_interceptions = avg_ball_recoveries = avg_saves = None

    # Update club statistics
    club_stats.matches_played = matches_played
    club_stats.wins = wins
    club_stats.draws = draws
    club_stats.losses = losses
    club_stats.goals_scored = goals_scored
    club_stats.goals_conceded = goals_conceded
    club_stats.total_clean_sheets = clean_sheets
    club_stats.avg_goals_per_match = Decimal(str(goals_scored / matches_played)) if matches_played > 0 else None
    club_stats.avg_goals_conceded_per_match = Decimal(str(goals_conceded / matches_played)) if matches_played > 0 else None
    club_stats.avg_possession_percentage = Decimal(str(round(avg_possession, 2))) if avg_possession else None
    club_stats.avg_xg_per_match = Decimal(str(round(avg_xg, 2))) if avg_xg else None
    club_stats.avg_total_shots = Decimal(str(round(avg_shots, 2))) if avg_shots else None
    club_stats.avg_shots_on_target = Decimal(str(round(avg_shots_on_target, 2))) if avg_shots_on_target else None
    club_stats.avg_total_passes = Decimal(str(round(avg_passes, 2))) if avg_passes else None
    club_stats.pass_completion_rate = Decimal(str(round(pass_completion, 2))) if pass_completion else None
    club_stats.avg_final_third_passes = Decimal(str(round(avg_final_third, 2))) if avg_final_third else None
    club_stats.avg_crosses = Decimal(str(round(avg_crosses, 2))) if avg_crosses else None
    club_stats.avg_dribbles = Decimal(str(round(avg_dribbles, 2))) if avg_dribbles else None
    club_stats.avg_successful_dribbles = Decimal(str(round(avg_successful_dribbles, 2))) if avg_successful_dribbles else None
    club_stats.avg_tackles = Decimal(str(round(avg_tackles, 2))) if avg_tackles else None
    club_stats.avg_interceptions = Decimal(str(round(avg_interceptions, 2))) if avg_interceptions else None
    club_stats.avg_ball_recoveries = Decimal(str(round(avg_ball_recoveries, 2))) if avg_ball_recoveries else None
    club_stats.avg_saves_per_match = Decimal(str(round(avg_saves, 2))) if avg_saves else None
    club_stats.updated_at = datetime.now(timezone.utc)

    db.flush()
    db.refresh(club_stats)

    return club_stats
