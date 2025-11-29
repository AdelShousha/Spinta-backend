"""
Service for calculating and updating club season statistics.

This service aggregates match-level data from matches, goals, match_statistics,
and player_match_statistics tables to compute season-level statistics for clubs.
"""

from uuid import UUID
from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models.match import Match
from app.models.goal import Goal
from app.models.match_statistics import MatchStatistics
from app.models.player_match_statistics import PlayerMatchStatistics
from app.models.club_season_statistics import ClubSeasonStatistics


def calculate_club_season_statistics(club_id: UUID, db: Session) -> Dict[str, Any]:
    """
    Calculate all season statistics for a club from match-level data.

    This is a pure calculation function that queries the database but does not
    modify any records. Returns a dictionary with all 27 statistics fields.

    Args:
        club_id: The UUID of the club
        db: SQLAlchemy database session

    Returns:
        Dictionary containing all 27 season statistics fields
    """
    # Get all match IDs for this club
    match_ids_query = db.query(Match.match_id).filter(Match.club_id == club_id)
    match_ids = [m[0] for m in match_ids_query.all()]

    # Initialize result dictionary
    result: Dict[str, Any] = {}

    # ==========================================================================
    # BASIC COUNTS FROM MATCHES TABLE
    # ==========================================================================

    matches_query = db.query(
        func.count(Match.match_id).label('matches_played'),
        func.sum(case((Match.result == 'W', 1), else_=0)).label('wins'),
        func.sum(case((Match.result == 'D', 1), else_=0)).label('draws'),
        func.sum(case((Match.result == 'L', 1), else_=0)).label('losses'),
        func.sum(case((Match.opponent_score == 0, 1), else_=0)).label('total_clean_sheets')
    ).filter(Match.club_id == club_id).first()

    result['matches_played'] = matches_query.matches_played or 0
    result['wins'] = matches_query.wins or 0
    result['draws'] = matches_query.draws or 0
    result['losses'] = matches_query.losses or 0
    result['total_clean_sheets'] = matches_query.total_clean_sheets or 0

    # ==========================================================================
    # GOALS FROM GOALS TABLE
    # ==========================================================================

    if len(match_ids) > 0:
        goals_query = db.query(
            func.sum(case((Goal.is_our_goal == True, 1), else_=0)).label('goals_scored'),
            func.sum(case((Goal.is_our_goal == False, 1), else_=0)).label('goals_conceded')
        ).filter(Goal.match_id.in_(match_ids)).first()

        result['goals_scored'] = goals_query.goals_scored or 0
        result['goals_conceded'] = goals_query.goals_conceded or 0
    else:
        result['goals_scored'] = 0
        result['goals_conceded'] = 0

    # ==========================================================================
    # TOTAL ASSISTS FROM PLAYER_MATCH_STATISTICS
    # ==========================================================================

    if len(match_ids) > 0:
        assists_query = db.query(
            func.sum(PlayerMatchStatistics.assists).label('total_assists')
        ).filter(PlayerMatchStatistics.match_id.in_(match_ids)).first()

        result['total_assists'] = assists_query.total_assists or 0
    else:
        result['total_assists'] = 0

    # ==========================================================================
    # TEAM FORM (Last 5 matches, most recent on LEFT)
    # ==========================================================================

    last_5_matches = db.query(Match.result).filter(
        Match.club_id == club_id,
        Match.result.isnot(None)
    ).order_by(Match.match_date.desc()).limit(5).all()

    # Concatenate results with most recent first (already ordered DESC)
    result['team_form'] = ''.join([m.result for m in last_5_matches]) if last_5_matches else ''

    # ==========================================================================
    # CALCULATED RATIOS (goals per match, goals conceded per match)
    # ==========================================================================

    matches_played = result['matches_played']

    if matches_played > 0:
        result['avg_goals_per_match'] = Decimal(str(result['goals_scored'])) / Decimal(str(matches_played))
        result['avg_goals_per_match'] = result['avg_goals_per_match'].quantize(Decimal('0.01'))

        result['avg_goals_conceded_per_match'] = Decimal(str(result['goals_conceded'])) / Decimal(str(matches_played))
        result['avg_goals_conceded_per_match'] = result['avg_goals_conceded_per_match'].quantize(Decimal('0.01'))
    else:
        result['avg_goals_per_match'] = None
        result['avg_goals_conceded_per_match'] = None

    # ==========================================================================
    # SIMPLE AVERAGES FROM MATCH_STATISTICS
    # ==========================================================================

    if len(match_ids) > 0:
        avg_query = db.query(
            func.avg(MatchStatistics.possession_percentage).label('avg_possession_percentage'),
            func.avg(MatchStatistics.total_shots).label('avg_total_shots'),
            func.avg(MatchStatistics.shots_on_target).label('avg_shots_on_target'),
            func.avg(MatchStatistics.expected_goals).label('avg_xg_per_match'),
            func.avg(MatchStatistics.total_passes).label('avg_total_passes'),
            func.avg(MatchStatistics.passes_in_final_third).label('avg_final_third_passes'),
            func.avg(MatchStatistics.crosses).label('avg_crosses'),
            func.avg(MatchStatistics.total_dribbles).label('avg_dribbles'),
            func.avg(MatchStatistics.successful_dribbles).label('avg_successful_dribbles'),
            func.avg(MatchStatistics.total_tackles).label('avg_tackles'),
            func.avg(MatchStatistics.interceptions).label('avg_interceptions'),
            func.avg(MatchStatistics.ball_recoveries).label('avg_ball_recoveries'),
            func.avg(MatchStatistics.goalkeeper_saves).label('avg_saves_per_match')
        ).filter(
            MatchStatistics.match_id.in_(match_ids),
            MatchStatistics.team_type == 'our_team'
        ).first()

        # Convert to Decimal with 2 decimal places
        result['avg_possession_percentage'] = _round_decimal(avg_query.avg_possession_percentage, 2)
        result['avg_total_shots'] = _round_decimal(avg_query.avg_total_shots, 2)
        result['avg_shots_on_target'] = _round_decimal(avg_query.avg_shots_on_target, 2)
        result['avg_xg_per_match'] = _round_decimal(avg_query.avg_xg_per_match, 2)
        result['avg_total_passes'] = _round_decimal(avg_query.avg_total_passes, 2)
        result['avg_final_third_passes'] = _round_decimal(avg_query.avg_final_third_passes, 2)
        result['avg_crosses'] = _round_decimal(avg_query.avg_crosses, 2)
        result['avg_dribbles'] = _round_decimal(avg_query.avg_dribbles, 2)
        result['avg_successful_dribbles'] = _round_decimal(avg_query.avg_successful_dribbles, 2)
        result['avg_tackles'] = _round_decimal(avg_query.avg_tackles, 2)
        result['avg_interceptions'] = _round_decimal(avg_query.avg_interceptions, 2)
        result['avg_ball_recoveries'] = _round_decimal(avg_query.avg_ball_recoveries, 2)
        result['avg_saves_per_match'] = _round_decimal(avg_query.avg_saves_per_match, 2)
    else:
        # No matches - set all averages to None
        result['avg_possession_percentage'] = None
        result['avg_total_shots'] = None
        result['avg_shots_on_target'] = None
        result['avg_xg_per_match'] = None
        result['avg_total_passes'] = None
        result['avg_final_third_passes'] = None
        result['avg_crosses'] = None
        result['avg_dribbles'] = None
        result['avg_successful_dribbles'] = None
        result['avg_tackles'] = None
        result['avg_interceptions'] = None
        result['avg_ball_recoveries'] = None
        result['avg_saves_per_match'] = None

    # ==========================================================================
    # WEIGHTED AVERAGES
    # ==========================================================================

    # Pass completion rate (weighted)
    if len(match_ids) > 0:
        pass_sums = db.query(
            func.sum(MatchStatistics.total_passes).label('total_passes'),
            func.sum(MatchStatistics.passes_completed).label('passes_completed')
        ).filter(
            MatchStatistics.match_id.in_(match_ids),
            MatchStatistics.team_type == 'our_team'
        ).first()

        if pass_sums.total_passes and pass_sums.total_passes > 0:
            pass_completion_rate = (Decimal(str(pass_sums.passes_completed)) /
                                   Decimal(str(pass_sums.total_passes))) * Decimal('100')
            result['pass_completion_rate'] = pass_completion_rate.quantize(Decimal('0.01'))
        else:
            result['pass_completion_rate'] = None
    else:
        result['pass_completion_rate'] = None

    # Tackle success rate (weighted - back-calculated from percentages)
    if len(match_ids) > 0:
        tackle_data = db.query(
            MatchStatistics.total_tackles,
            MatchStatistics.tackle_success_percentage
        ).filter(
            MatchStatistics.match_id.in_(match_ids),
            MatchStatistics.team_type == 'our_team',
            MatchStatistics.total_tackles.isnot(None)
        ).all()

        total_tackles = 0
        total_successful = Decimal('0')

        for tackles, success_pct in tackle_data:
            if tackles and success_pct:
                total_tackles += tackles
                total_successful += Decimal(str(tackles)) * (Decimal(str(success_pct)) / Decimal('100'))

        if total_tackles > 0:
            tackle_success_rate = (total_successful / Decimal(str(total_tackles))) * Decimal('100')
            result['tackle_success_rate'] = tackle_success_rate.quantize(Decimal('0.01'))
        else:
            result['tackle_success_rate'] = None
    else:
        result['tackle_success_rate'] = None

    # Interception success rate (weighted - from player_match_statistics)
    if len(match_ids) > 0:
        interception_data = db.query(
            PlayerMatchStatistics.interceptions,
            PlayerMatchStatistics.interception_success_rate
        ).filter(
            PlayerMatchStatistics.match_id.in_(match_ids),
            PlayerMatchStatistics.interceptions.isnot(None),
            PlayerMatchStatistics.interceptions > 0
        ).all()

        total_interceptions = 0
        total_successful = Decimal('0')

        for interceptions, success_rate in interception_data:
            if interceptions:
                total_interceptions += interceptions
                if success_rate:  # Handle NULL
                    total_successful += Decimal(str(interceptions)) * (Decimal(str(success_rate)) / Decimal('100'))
                # else: treat as 0% success (contributes 0 to total_successful)

        if total_interceptions > 0:
            interception_success_rate = (total_successful / Decimal(str(total_interceptions))) * Decimal('100')
            result['interception_success_rate'] = interception_success_rate.quantize(Decimal('0.01'))
        else:
            result['interception_success_rate'] = None
    else:
        result['interception_success_rate'] = None

    return result


def update_club_season_statistics(db: Session, club_id: UUID) -> bool:
    """
    Update (or create) the ClubSeasonStatistics record for a club.

    This function:
    1. Calls the helper function to calculate all statistics
    2. Updates existing record or creates new one (upsert)
    3. Commits the transaction to the database

    Args:
        db: SQLAlchemy database session
        club_id: The UUID of the club

    Returns:
        True if successful
    """
    # Calculate all statistics
    stats_data = calculate_club_season_statistics(club_id, db)

    # Check if record already exists
    existing = db.query(ClubSeasonStatistics).filter_by(club_id=club_id).first()

    if existing:
        # Update existing record
        for key, value in stats_data.items():
            setattr(existing, key, value)
    else:
        # Create new record
        new_stats = ClubSeasonStatistics(
            club_id=club_id,
            **stats_data
        )
        db.add(new_stats)

    # Commit transaction
    db.commit()

    return True


def _round_decimal(value: Optional[float], places: int) -> Optional[Decimal]:
    """
    Helper function to round a float/Decimal to specified decimal places.

    Args:
        value: The value to round (can be None)
        places: Number of decimal places

    Returns:
        Decimal rounded to specified places, or None if input is None
    """
    if value is None:
        return None

    decimal_value = Decimal(str(value))
    quantizer = Decimal('0.1') ** places
    return decimal_value.quantize(quantizer)
