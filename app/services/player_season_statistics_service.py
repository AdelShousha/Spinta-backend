"""
Service for calculating and updating player season statistics.

This service aggregates match-level data from player_match_statistics table
to compute season-level statistics for individual players.

Includes:
- 11 simple aggregations (matches, goals, assists, etc.)
- 2 calculated averages (shots per game)
- 2 weighted percentages (tackle success, interception success)
- 5 attribute ratings with 25-100 normalization and low match count boost
"""

from uuid import UUID
from decimal import Decimal
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.player_match_statistics import PlayerMatchStatistics
from app.models.player_season_statistics import PlayerSeasonStatistics


def calculate_player_season_statistics(player_id: UUID, db: Session) -> Dict[str, Any]:
    """
    Calculate all season statistics for a player from match-level data.

    This is a pure calculation function that queries the database but does not
    modify any records. Returns a dictionary with all 17 statistics fields.

    Args:
        player_id: The UUID of the player
        db: SQLAlchemy database session

    Returns:
        Dictionary containing all 17 season statistics fields
    """
    # Initialize result dictionary
    result: Dict[str, Any] = {}

    # ==========================================================================
    # AGGREGATIONS - Single query for efficiency
    # ==========================================================================

    agg_query = db.query(
        func.count(PlayerMatchStatistics.player_match_stats_id).label('matches_played'),
        func.sum(PlayerMatchStatistics.goals).label('total_goals'),
        func.sum(PlayerMatchStatistics.assists).label('total_assists'),
        func.sum(PlayerMatchStatistics.expected_goals).label('total_expected_goals'),
        func.sum(PlayerMatchStatistics.shots).label('total_shots'),
        func.sum(PlayerMatchStatistics.shots_on_target).label('total_shots_on_target'),
        func.sum(PlayerMatchStatistics.total_passes).label('total_passes'),
        func.sum(PlayerMatchStatistics.completed_passes).label('passes_completed'),
        func.sum(PlayerMatchStatistics.final_third_passes).label('total_final_third_passes'),
        func.sum(PlayerMatchStatistics.crosses).label('total_crosses'),
        func.sum(PlayerMatchStatistics.total_dribbles).label('total_dribbles'),
        func.sum(PlayerMatchStatistics.successful_dribbles).label('successful_dribbles'),
        func.sum(PlayerMatchStatistics.tackles).label('total_tackles'),
        func.sum(PlayerMatchStatistics.interceptions).label('total_interceptions')
    ).filter(PlayerMatchStatistics.player_id == player_id).first()

    # Extract simple aggregations
    matches_played = agg_query.matches_played or 0
    result['matches_played'] = matches_played
    result['goals'] = agg_query.total_goals or 0
    result['assists'] = agg_query.total_assists or 0
    result['expected_goals'] = agg_query.total_expected_goals  # Can be NULL
    result['total_passes'] = agg_query.total_passes  # Can be NULL
    result['passes_completed'] = agg_query.passes_completed  # Can be NULL
    result['total_dribbles'] = agg_query.total_dribbles  # Can be NULL
    result['successful_dribbles'] = agg_query.successful_dribbles  # Can be NULL
    result['tackles'] = agg_query.total_tackles  # Can be NULL
    result['interceptions'] = agg_query.total_interceptions  # Can be NULL

    # Store for rating calculations
    total_shots = agg_query.total_shots or 0
    total_shots_on_target = agg_query.total_shots_on_target or 0
    total_final_third_passes = agg_query.total_final_third_passes or 0
    total_crosses = agg_query.total_crosses or 0

    # ==========================================================================
    # CALCULATED AVERAGES (shots per game)
    # ==========================================================================

    if matches_played > 0:
        shots_per_game = Decimal(str(total_shots)) / Decimal(str(matches_played))
        result['shots_per_game'] = shots_per_game.quantize(Decimal('0.01'))

        shots_on_target_per_game = Decimal(str(total_shots_on_target)) / Decimal(str(matches_played))
        result['shots_on_target_per_game'] = shots_on_target_per_game.quantize(Decimal('0.01'))
    else:
        result['shots_per_game'] = None
        result['shots_on_target_per_game'] = None

    # ==========================================================================
    # WEIGHTED PERCENTAGES (tackle and interception success rates)
    # ==========================================================================

    # Tackle success rate - back-calculate from match percentages
    tackle_data = db.query(
        PlayerMatchStatistics.tackles,
        PlayerMatchStatistics.tackle_success_rate
    ).filter(
        PlayerMatchStatistics.player_id == player_id,
        PlayerMatchStatistics.tackles.isnot(None),
        PlayerMatchStatistics.tackles > 0
    ).all()

    total_tackles = 0
    total_successful_tackles = Decimal('0')

    for tackles, success_pct in tackle_data:
        if tackles:
            total_tackles += tackles
            if success_pct:  # Handle NULL success rate
                total_successful_tackles += Decimal(str(tackles)) * (Decimal(str(success_pct)) / Decimal('100'))
            # else: treat as 0% success (contributes 0 to total_successful_tackles)

    if total_tackles > 0:
        tackle_success_rate = (total_successful_tackles / Decimal(str(total_tackles))) * Decimal('100')
        result['tackle_success_rate'] = tackle_success_rate.quantize(Decimal('0.01'))
    else:
        result['tackle_success_rate'] = None

    # Interception success rate - back-calculate from match percentages
    interception_data = db.query(
        PlayerMatchStatistics.interceptions,
        PlayerMatchStatistics.interception_success_rate
    ).filter(
        PlayerMatchStatistics.player_id == player_id,
        PlayerMatchStatistics.interceptions.isnot(None),
        PlayerMatchStatistics.interceptions > 0
    ).all()

    total_interceptions = 0
    total_successful_interceptions = Decimal('0')

    for interceptions, success_rate in interception_data:
        if interceptions:
            total_interceptions += interceptions
            if success_rate:  # Handle NULL success rate
                total_successful_interceptions += Decimal(str(interceptions)) * (Decimal(str(success_rate)) / Decimal('100'))
            # else: treat as 0% success

    if total_interceptions > 0:
        interception_success_rate = (total_successful_interceptions / Decimal(str(total_interceptions))) * Decimal('100')
        result['interception_success_rate'] = interception_success_rate.quantize(Decimal('0.01'))
    else:
        result['interception_success_rate'] = None

    # ==========================================================================
    # ATTRIBUTE RATINGS (5 ratings with 25-100 normalization)
    # ==========================================================================

    # Calculate all 5 ratings
    result['attacking_rating'] = _calculate_attacking_rating(result, matches_played, total_shots)
    result['technique_rating'] = _calculate_technique_rating(result, matches_played, total_shots, total_shots_on_target)
    result['tactical_rating'] = _calculate_tactical_rating(result, matches_played, total_final_third_passes, total_crosses)
    result['defending_rating'] = _calculate_defending_rating(result, matches_played)
    result['creativity_rating'] = _calculate_creativity_rating(result, matches_played, total_final_third_passes, total_crosses)

    return result


def update_player_season_statistics(db: Session, player_ids: List[UUID]) -> int:
    """
    Update (or create) PlayerSeasonStatistics records for multiple players.

    This function:
    1. Calls the helper function to calculate all statistics for each player
    2. Updates existing record or creates new one (upsert)
    3. Commits the transaction to the database

    Args:
        db: SQLAlchemy database session
        player_ids: List of player UUIDs to update

    Returns:
        Count of players updated
    """
    count = 0

    for player_id in player_ids:
        # Calculate all statistics for this player
        stats_data = calculate_player_season_statistics(player_id, db)

        # Check if record already exists
        existing = db.query(PlayerSeasonStatistics).filter_by(player_id=player_id).first()

        if existing:
            # Update existing record
            for key, value in stats_data.items():
                setattr(existing, key, value)
        else:
            # Create new record
            new_stats = PlayerSeasonStatistics(
                player_id=player_id,
                **stats_data
            )
            db.add(new_stats)

        count += 1

    # Commit transaction
    db.commit()

    return count


# =============================================================================
# HELPER FUNCTIONS - Rating Calculations
# =============================================================================

def _calculate_attacking_rating(stats: Dict[str, Any], matches_played: int, total_shots: int) -> int:
    """
    Calculate attacking rating (25-100 scale with low match boost).

    Components:
    - Goals (40%)
    - Assists (30%)
    - Expected goals (20%)
    - Shots per game (10%)
    """
    if matches_played == 0:
        return 25  # Baseline, no boost

    goals = stats.get('goals', 0)
    assists = stats.get('assists', 0)
    xg = float(stats.get('expected_goals') or 0)
    shots_pg = float(stats.get('shots_per_game') or 0)

    # Normalize components to 0-1 scale
    goals_score = min(goals / 30.0, 1.0)  # 30 goals = max
    assists_score = min(assists / 20.0, 1.0)  # 20 assists = max
    xg_score = min(xg / 25.0, 1.0)  # 25 xG = max
    shots_pg_score = min(shots_pg / 5.0, 1.0)  # 5 shots/game = max

    # Weighted average
    raw_score = (
        goals_score * 0.40 +
        assists_score * 0.30 +
        xg_score * 0.20 +
        shots_pg_score * 0.10
    )

    # Apply low match count boost
    raw_score = _apply_match_count_boost(raw_score, matches_played)

    # Normalize to 25-100 range
    return int(25 + (raw_score * 75))


def _calculate_technique_rating(
    stats: Dict[str, Any],
    matches_played: int,
    total_shots: int,
    total_shots_on_target: int
) -> int:
    """
    Calculate technique rating (25-100 scale with low match boost).

    Components:
    - Dribble success percentage (40%)
    - Pass completion percentage (30%)
    - Shot accuracy percentage (20%)
    - Dribble volume (10%)
    """
    if matches_played == 0:
        return 25  # Baseline, no boost

    total_dribbles = stats.get('total_dribbles') or 0
    successful_dribbles = stats.get('successful_dribbles') or 0
    total_passes = stats.get('total_passes') or 0
    passes_completed = stats.get('passes_completed') or 0

    # Calculate percentages (0-1 scale)
    dribble_success_pct = (successful_dribbles / total_dribbles) if total_dribbles else 0
    pass_completion_pct = (passes_completed / total_passes) if total_passes else 0
    shot_accuracy_pct = (total_shots_on_target / total_shots) if total_shots else 0

    # Volume component
    dribble_volume_score = min(total_dribbles / 100.0, 1.0)  # 100 dribbles = max

    # Weighted average
    raw_score = (
        dribble_success_pct * 0.40 +
        pass_completion_pct * 0.30 +
        shot_accuracy_pct * 0.20 +
        dribble_volume_score * 0.10
    )

    # Apply low match count boost
    raw_score = _apply_match_count_boost(raw_score, matches_played)

    # Normalize to 25-100 range
    return int(25 + (raw_score * 75))


def _calculate_tactical_rating(
    stats: Dict[str, Any],
    matches_played: int,
    total_final_third_passes: int,
    total_crosses: int
) -> int:
    """
    Calculate tactical rating (25-100 scale with low match boost).

    Components:
    - Final third passes (30%)
    - Total passes (25%)
    - Pass completion rate (25%)
    - Crosses (20%)
    """
    if matches_played == 0:
        return 25  # Baseline, no boost

    total_passes = stats.get('total_passes') or 0
    passes_completed = stats.get('passes_completed') or 0

    # Normalize volumes
    final_third_score = min(total_final_third_passes / 150.0, 1.0)  # 150 = max
    total_passes_score = min(total_passes / 1500.0, 1.0)  # 1500 = max
    pass_comp_score = (passes_completed / total_passes) if total_passes else 0
    crosses_score = min(total_crosses / 50.0, 1.0)  # 50 crosses = max

    # Weighted average
    raw_score = (
        final_third_score * 0.30 +
        total_passes_score * 0.25 +
        pass_comp_score * 0.25 +
        crosses_score * 0.20
    )

    # Apply low match count boost
    raw_score = _apply_match_count_boost(raw_score, matches_played)

    # Normalize to 25-100 range
    return int(25 + (raw_score * 75))


def _calculate_defending_rating(stats: Dict[str, Any], matches_played: int) -> int:
    """
    Calculate defending rating (25-100 scale with low match boost).

    Components:
    - Tackles (35%)
    - Interceptions (35%)
    - Tackle success rate (20%)
    - Interception success rate (10%)
    """
    if matches_played == 0:
        return 25  # Baseline, no boost

    tackles = stats.get('tackles') or 0
    interceptions = stats.get('interceptions') or 0
    tackle_success_rate = stats.get('tackle_success_rate')
    interception_success_rate = stats.get('interception_success_rate')

    # Normalize defensive actions
    tackles_score = min(tackles / 80.0, 1.0)  # 80 tackles = max
    interceptions_score = min(interceptions / 60.0, 1.0)  # 60 interceptions = max

    # Success rates (0-100 to 0-1 scale)
    tackle_success_score = (float(tackle_success_rate) / 100.0) if tackle_success_rate else 0
    interception_success_score = (float(interception_success_rate) / 100.0) if interception_success_rate else 0

    # Weighted average
    raw_score = (
        tackles_score * 0.35 +
        interceptions_score * 0.35 +
        tackle_success_score * 0.20 +
        interception_success_score * 0.10
    )

    # Apply low match count boost
    raw_score = _apply_match_count_boost(raw_score, matches_played)

    # Normalize to 25-100 range
    return int(25 + (raw_score * 75))


def _calculate_creativity_rating(
    stats: Dict[str, Any],
    matches_played: int,
    total_final_third_passes: int,
    total_crosses: int
) -> int:
    """
    Calculate creativity rating (25-100 scale with low match boost).

    Components:
    - Assists (40%)
    - Final third passes (30%)
    - Assist/goal ratio (20%)
    - Crosses (10%)
    """
    if matches_played == 0:
        return 25  # Baseline, no boost

    assists = stats.get('assists', 0)
    goals = stats.get('goals', 0)

    # Normalize components
    assists_score = min(assists / 15.0, 1.0)  # 15 assists = max
    final_third_score = min(total_final_third_passes / 150.0, 1.0)  # 150 = max

    # Assist/goal ratio as proxy for expected assists contribution
    if goals > 0:
        xg_contribution_score = min((assists / (goals + 1)) / 1.5, 1.0)
    else:
        xg_contribution_score = 1.0 if assists > 0 else 0

    crosses_score = min(total_crosses / 50.0, 1.0)  # 50 crosses = max

    # Weighted average
    raw_score = (
        assists_score * 0.40 +
        final_third_score * 0.30 +
        xg_contribution_score * 0.20 +
        crosses_score * 0.10
    )

    # Apply low match count boost
    raw_score = _apply_match_count_boost(raw_score, matches_played)

    # Normalize to 25-100 range
    return int(25 + (raw_score * 75))


def _apply_match_count_boost(raw_score: float, matches_played: int) -> float:
    """
    Apply boost factor for players with low match count.

    Boost logic:
    - 4 matches: 1.10x boost (10%)
    - 3 matches: 1.20x boost (20%)
    - 2 matches: 1.30x boost (30%)
    - 1 match:   1.50x boost (50%)
    - 0 matches: No boost (N/A, ratings should be 25 baseline)

    Args:
        raw_score: Raw score in 0-1 range
        matches_played: Number of matches played

    Returns:
        Boosted score capped at 1.0
    """
    if matches_played < 5 and matches_played > 0:
        boost_factor = 1.0 + (0.10 * (5 - matches_played))
        return min(raw_score * boost_factor, 1.0)
    return raw_score
