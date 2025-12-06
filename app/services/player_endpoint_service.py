"""
Player endpoint service module.

Provides player-facing operations including:
- Dashboard data retrieval
- Match list and detail retrieval
- Training plan viewing and exercise completion
- Profile retrieval

All functions use db.flush() and let the caller handle db.commit() and db.rollback().
"""

from uuid import UUID
from datetime import date, datetime, timezone
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.player import Player
from app.models.club import Club
from app.models.match import Match
from app.models.player_match_statistics import PlayerMatchStatistics
from app.models.player_season_statistics import PlayerSeasonStatistics
from app.models.training_plan import TrainingPlan
from app.models.training_exercise import TrainingExercise
from app.models.opponent_club import OpponentClub

# Import helper from coach_service
from app.services.coach_service import calculate_age


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _default_zero(value: Any) -> Any:
    """
    Convert None to 0 for numeric stats.

    Args:
        value: The value to check

    Returns:
        The original value if not None, otherwise 0
    """
    return value if value is not None else 0


# ============================================================================
# OWNERSHIP VERIFICATION FUNCTIONS
# ============================================================================

def verify_player_match_participation(
    db: Session,
    player_id: UUID,
    match_id: UUID
) -> PlayerMatchStatistics:
    """
    Verify player participated in match.

    Args:
        db: Database session
        player_id: Player UUID from JWT
        match_id: Match UUID

    Returns:
        PlayerMatchStatistics record

    Raises:
        ValueError: If player didn't participate or match not found
    """
    stats = (
        db.query(PlayerMatchStatistics)
        .filter(
            PlayerMatchStatistics.player_id == player_id,
            PlayerMatchStatistics.match_id == match_id
        )
        .first()
    )

    if not stats:
        raise ValueError("Match not found or you did not play in this match")

    return stats


def verify_player_training_plan(
    db: Session,
    plan_id: UUID,
    player_id: UUID
) -> TrainingPlan:
    """
    Verify training plan belongs to player.

    Args:
        db: Database session
        plan_id: Training plan UUID
        player_id: Player UUID from JWT

    Returns:
        TrainingPlan instance

    Raises:
        ValueError: If plan not found or not assigned to player
    """
    plan = db.query(TrainingPlan).filter(TrainingPlan.plan_id == plan_id).first()

    if not plan:
        raise ValueError("Training plan not found")

    if str(plan.player_id) != str(player_id):
        raise ValueError("This training plan is not assigned to you")

    return plan


def verify_player_exercise(
    db: Session,
    exercise_id: UUID,
    player_id: UUID
) -> Tuple[TrainingExercise, TrainingPlan]:
    """
    Verify exercise belongs to player's training plan.

    Args:
        db: Database session
        exercise_id: Exercise UUID
        player_id: Player UUID from JWT

    Returns:
        Tuple of (exercise, plan)

    Raises:
        ValueError: If exercise not found or not part of player's plan
    """
    exercise = (
        db.query(TrainingExercise)
        .filter(TrainingExercise.exercise_id == exercise_id)
        .first()
    )

    if not exercise:
        raise ValueError("Exercise not found")

    # Verify plan belongs to player
    plan = db.query(TrainingPlan).filter(TrainingPlan.plan_id == exercise.plan_id).first()

    if not plan or str(plan.player_id) != str(player_id):
        raise ValueError("This exercise is not part of your training plan")

    return exercise, plan


# ============================================================================
# DASHBOARD SERVICE
# ============================================================================

def get_player_dashboard(db: Session, player_id: UUID) -> Dict[str, Any]:
    """
    Get player dashboard data (My Stats tab).

    Args:
        db: Database session
        player_id: Player UUID from JWT

    Returns:
        Dict matching PlayerDashboardResponse schema:
        - player info with calculated age
        - attributes (5 ratings)
        - season_statistics grouped by category

    Raises:
        ValueError: If player not found
    """
    # Get player basic info
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise ValueError("Player not found")

    # Calculate age from birth_date
    age_str = calculate_age(player.birth_date)

    # Get season statistics
    season_stats = (
        db.query(PlayerSeasonStatistics)
        .filter(PlayerSeasonStatistics.player_id == player_id)
        .first()
    )

    # Build response structure
    return {
        "player": {
            "player_id": str(player.player_id),
            "player_name": player.player_name,
            "jersey_number": player.jersey_number,
            "height": player.height,
            "age": age_str,
            "profile_image_url": player.profile_image_url
        },
        "attributes": {
            "attacking_rating": _default_zero(season_stats.attacking_rating if season_stats else None),
            "technique_rating": _default_zero(season_stats.technique_rating if season_stats else None),
            "creativity_rating": _default_zero(season_stats.creativity_rating if season_stats else None),
            "tactical_rating": _default_zero(season_stats.tactical_rating if season_stats else None),
            "defending_rating": _default_zero(season_stats.defending_rating if season_stats else None)
        },
        "season_statistics": {
            "general": {
                "matches_played": _default_zero(season_stats.matches_played if season_stats else None)
            },
            "attacking": {
                "goals": season_stats.goals if season_stats else 0,
                "assists": season_stats.assists if season_stats else 0,
                "expected_goals": float(_default_zero(season_stats.expected_goals if season_stats else None)),
                "shots_per_game": float(_default_zero(season_stats.shots_per_game if season_stats else None)),
                "shots_on_target_per_game": float(_default_zero(season_stats.shots_on_target_per_game if season_stats else None))
            },
            "passing": {
                "total_passes": _default_zero(season_stats.total_passes if season_stats else None),
                "passes_completed": _default_zero(season_stats.passes_completed if season_stats else None)
            },
            "dribbling": {
                "total_dribbles": _default_zero(season_stats.total_dribbles if season_stats else None),
                "successful_dribbles": _default_zero(season_stats.successful_dribbles if season_stats else None)
            },
            "defending": {
                "tackles": _default_zero(season_stats.tackles if season_stats else None),
                "tackle_success_rate": float(_default_zero(season_stats.tackle_success_rate if season_stats else None)),
                "interceptions": _default_zero(season_stats.interceptions if season_stats else None),
                "interception_success_rate": float(_default_zero(season_stats.interception_success_rate if season_stats else None))
            }
        }
    }


# ============================================================================
# MATCHES SERVICES
# ============================================================================

def get_player_matches(
    db: Session,
    player_id: UUID,
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get paginated list of matches player participated in.

    Args:
        db: Database session
        player_id: Player UUID from JWT
        limit: Number of matches to return (default 20)
        offset: Number to skip for pagination (default 0)

    Returns:
        Dict with total_count and matches list
    """
    # Get total count
    total_count = (
        db.query(func.count(PlayerMatchStatistics.match_id))
        .filter(PlayerMatchStatistics.player_id == player_id)
        .scalar()
    ) or 0

    # Get matches with JOIN
    results = (
        db.query(Match)
        .join(PlayerMatchStatistics, Match.match_id == PlayerMatchStatistics.match_id)
        .filter(PlayerMatchStatistics.player_id == player_id)
        .order_by(Match.match_date.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    matches = []
    for match in results:
        matches.append({
            "match_id": str(match.match_id),
            "opponent_name": match.opponent_name,
            "match_date": match.match_date,
            "our_score": match.our_score,
            "opponent_score": match.opponent_score,
            "result": match.result
        })

    return {
        "total_count": total_count,
        "matches": matches
    }


def get_player_match_detail(
    db: Session,
    player_id: UUID,
    match_id: UUID
) -> Dict[str, Any]:
    """
    Get player's performance in specific match.

    Args:
        db: Database session
        player_id: Player UUID from JWT
        match_id: Match UUID

    Returns:
        Dict with match info, teams, player_summary, statistics

    Raises:
        ValueError: If player didn't participate in match
    """
    # Verify participation and get stats
    player_stats = verify_player_match_participation(db, player_id, match_id)

    # Get match with club info
    match = db.query(Match).filter(Match.match_id == match_id).first()
    club = db.query(Club).filter(Club.club_id == match.club_id).first()
    player = db.query(Player).filter(Player.player_id == player_id).first()

    # Get opponent logo
    opponent_logo = None
    if match.opponent_club_id:
        opponent_club = (
            db.query(OpponentClub)
            .filter(OpponentClub.opponent_club_id == match.opponent_club_id)
            .first()
        )
        if opponent_club:
            opponent_logo = opponent_club.logo_url

    return {
        "match": {
            "match_id": str(match.match_id),
            "match_date": match.match_date,
            "our_score": match.our_score,
            "opponent_score": match.opponent_score,
            "result": match.result
        },
        "teams": {
            "our_club": {
                "club_id": str(club.club_id),
                "club_name": club.club_name,
                "logo_url": club.logo_url
            },
            "opponent": {
                "opponent_name": match.opponent_name,
                "logo_url": opponent_logo
            }
        },
        "player_summary": {
            "player_name": player.player_name,
            "goals": player_stats.goals or 0,
            "assists": player_stats.assists or 0
        },
        "statistics": {
            "attacking": {
                "goals": player_stats.goals or 0,
                "assists": player_stats.assists or 0,
                "xg": float(_default_zero(player_stats.expected_goals)),
                "total_shots": _default_zero(player_stats.shots),
                "shots_on_target": _default_zero(player_stats.shots_on_target),
                "total_dribbles": _default_zero(player_stats.total_dribbles),
                "successful_dribbles": _default_zero(player_stats.successful_dribbles)
            },
            "passing": {
                "total_passes": _default_zero(player_stats.total_passes),
                "passes_completed": _default_zero(player_stats.completed_passes),
                "short_passes": _default_zero(player_stats.short_passes),
                "long_passes": _default_zero(player_stats.long_passes),
                "final_third": _default_zero(player_stats.final_third_passes),
                "crosses": _default_zero(player_stats.crosses)
            },
            "defending": {
                "tackles": _default_zero(player_stats.tackles),
                "tackle_success_rate": float(_default_zero(player_stats.tackle_success_rate)),
                "interceptions": _default_zero(player_stats.interceptions),
                "interception_success_rate": float(_default_zero(player_stats.interception_success_rate))
            }
        }
    }


# ============================================================================
# TRAINING SERVICES
# ============================================================================

def get_player_training_plans(db: Session, player_id: UUID) -> Dict[str, Any]:
    """
    Get all training plans assigned to player.

    Args:
        db: Database session
        player_id: Player UUID from JWT

    Returns:
        Dict with training_plans list
    """
    plans = (
        db.query(TrainingPlan)
        .filter(TrainingPlan.player_id == player_id)
        .order_by(TrainingPlan.created_at.desc())
        .all()
    )

    training_plans = []
    for plan in plans:
        training_plans.append({
            "plan_id": str(plan.plan_id),
            "plan_name": plan.plan_name,
            "created_at": plan.created_at.date() if isinstance(plan.created_at, datetime) else plan.created_at,
            "status": plan.status
        })

    return {"training_plans": training_plans}


def get_player_training_plan_detail(
    db: Session,
    player_id: UUID,
    plan_id: UUID
) -> Dict[str, Any]:
    """
    Get training plan detail for player.

    Args:
        db: Database session
        player_id: Player UUID from JWT
        plan_id: Training plan UUID

    Returns:
        Dict with plan info, progress, exercises, coach_notes

    Raises:
        ValueError: If plan not found or not assigned to player
    """
    # Verify ownership
    plan = verify_player_training_plan(db, plan_id, player_id)

    # Get player info
    player = db.query(Player).filter(Player.player_id == player_id).first()

    # Get exercises
    exercises_query = (
        db.query(TrainingExercise)
        .filter(TrainingExercise.plan_id == plan_id)
        .order_by(TrainingExercise.exercise_order)
        .all()
    )

    # Calculate progress
    total = len(exercises_query)
    completed = sum(1 for ex in exercises_query if ex.completed)
    percentage = int((completed / total) * 100) if total > 0 else 0

    exercises = []
    for ex in exercises_query:
        exercises.append({
            "exercise_id": str(ex.exercise_id),
            "exercise_name": ex.exercise_name,
            "description": ex.description,
            "sets": ex.sets,
            "reps": ex.reps,
            "duration_minutes": ex.duration_minutes,
            "exercise_order": ex.exercise_order,
            "completed": ex.completed,
            "completed_at": ex.completed_at
        })

    return {
        "plan": {
            "plan_id": str(plan.plan_id),
            "plan_name": plan.plan_name,
            "player_name": player.player_name,
            "player_jersey": player.jersey_number,
            "status": plan.status,
            "created_at": plan.created_at.date() if isinstance(plan.created_at, datetime) else plan.created_at
        },
        "progress": {
            "percentage": percentage,
            "completed_exercises": completed,
            "total_exercises": total
        },
        "exercises": exercises,
        "coach_notes": plan.coach_notes
    }


def toggle_exercise_completion(
    db: Session,
    player_id: UUID,
    exercise_id: UUID,
    completed: bool
) -> Dict[str, Any]:
    """
    Toggle exercise completion status.

    Args:
        db: Database session
        player_id: Player UUID from JWT
        exercise_id: Exercise UUID
        completed: New completion status

    Returns:
        Dict with exercise_id, completed, completed_at, plan_progress

    Raises:
        ValueError: If exercise not found or not part of player's plan
    """
    # Verify ownership
    exercise, plan = verify_player_exercise(db, exercise_id, player_id)

    # Update exercise
    exercise.completed = completed
    exercise.completed_at = datetime.now(timezone.utc) if completed else None

    # Recalculate progress
    exercises = (
        db.query(TrainingExercise)
        .filter(TrainingExercise.plan_id == plan.plan_id)
        .all()
    )

    total = len(exercises)
    # Count completed (including the one we just updated)
    completed_count = sum(1 for e in exercises if e.exercise_id == exercise_id and completed) + \
                      sum(1 for e in exercises if e.exercise_id != exercise_id and e.completed)

    # Update plan status based on progress
    if completed_count == 0:
        plan.status = "pending"
    elif completed_count == total:
        plan.status = "completed"
    else:
        plan.status = "in_progress"

    db.flush()

    return {
        "exercise_id": str(exercise_id),
        "completed": completed,
        "completed_at": exercise.completed_at,
        "plan_progress": {
            "plan_id": str(plan.plan_id),
            "total_exercises": total,
            "completed_exercises": completed_count,
            "progress_percentage": int((completed_count / total) * 100) if total > 0 else 0,
            "plan_status": plan.status
        }
    }


# ============================================================================
# PROFILE SERVICE
# ============================================================================

def get_player_profile(db: Session, player_id: UUID) -> Dict[str, Any]:
    """
    Get player profile information.

    Args:
        db: Database session
        player_id: Player UUID from JWT

    Returns:
        Dict with player info, club info, season_summary

    Raises:
        ValueError: If player not found
    """
    # Get player with user relationship
    player = db.query(Player).filter(Player.player_id == player_id).first()

    if not player:
        raise ValueError("Player not found")

    # Get email from user relationship
    user = db.query(User).filter(User.user_id == player.user_id).first()
    email = user.email if user else None

    # Get club
    club = db.query(Club).filter(Club.club_id == player.club_id).first()

    # Get season summary
    season_stats = (
        db.query(PlayerSeasonStatistics)
        .filter(PlayerSeasonStatistics.player_id == player_id)
        .first()
    )

    return {
        "player": {
            "player_id": str(player.player_id),
            "player_name": player.player_name,
            "email": email,
            "jersey_number": player.jersey_number,
            "position": player.position,
            "height": player.height,
            "birth_date": player.birth_date,
            "profile_image_url": player.profile_image_url
        },
        "club": {
            "club_name": club.club_name if club else None
        },
        "season_summary": {
            "matches_played": season_stats.matches_played if season_stats else 0,
            "goals": season_stats.goals if season_stats else 0,
            "assists": season_stats.assists if season_stats else 0
        }
    }
