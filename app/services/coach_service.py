"""
Coach service module.

Provides coach-related operations including:
- Dashboard data retrieval
- Match detail retrieval
- Player management and statistics
- Coach profile management
- Training plan CRUD operations

All functions use db.flush() and let the caller handle db.commit() and db.rollback().
"""

from uuid import UUID
from datetime import date, datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models.user import User
from app.models.coach import Coach
from app.models.club import Club
from app.models.player import Player
from app.models.player_season_statistics import PlayerSeasonStatistics
from app.models.club_season_statistics import ClubSeasonStatistics
from app.models.match import Match
from app.models.match_statistics import MatchStatistics
from app.models.match_lineup import MatchLineup
from app.models.goal import Goal
from app.models.player_match_statistics import PlayerMatchStatistics
from app.models.opponent_club import OpponentClub
from app.models.training_plan import TrainingPlan
from app.models.training_exercise import TrainingExercise


# ============================================================================
# HELPER FUNCTIONS (No database operations, pure logic)
# ============================================================================

def calculate_age(birth_date: Optional[date]) -> Optional[str]:
    """
    Calculate age string from birth date.

    Args:
        birth_date: Birth date

    Returns:
        Age string in format "X years" or None if birth_date is None
    """
    if not birth_date:
        return None

    today = date.today()
    age = today.year - birth_date.year

    # Adjust if birthday hasn't occurred yet this year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return f"{age} years"


def _build_stat_comparison(our_val: Any, opp_val: Any) -> Dict[str, Any]:
    """
    Build comparison dict for match statistics.

    Args:
        our_val: Our team's value
        opp_val: Opponent's value

    Returns:
        Dict with our_team and opponent keys
    """
    return {
        "our_team": our_val if our_val is not None else 0,
        "opponent": opp_val if opp_val is not None else 0
    }


def _calculate_win_rate(wins: int, matches_played: int) -> Optional[int]:
    """
    Calculate win rate percentage.

    Args:
        wins: Number of wins
        matches_played: Total matches played

    Returns:
        Win rate percentage (0-100) or None if no matches
    """
    if matches_played == 0:
        return None
    return int((wins / matches_played) * 100)


def _calculate_training_progress(exercises: List[TrainingExercise]) -> Dict[str, int]:
    """
    Calculate training plan progress.

    Args:
        exercises: List of training exercises

    Returns:
        Dict with percentage, completed_exercises, total_exercises
    """
    total = len(exercises)
    completed = sum(1 for ex in exercises if ex.completed)
    percentage = int((completed / total) * 100) if total > 0 else 0

    return {
        "percentage": percentage,
        "completed_exercises": completed,
        "total_exercises": total
    }


# ============================================================================
# OWNERSHIP VERIFICATION FUNCTIONS (Database queries for auth)
# ============================================================================

def get_coach_club(db: Session, user_id: UUID) -> Club:
    """
    Get club for authenticated coach user.

    Args:
        db: Database session
        user_id: User UUID from JWT token

    Returns:
        Club instance

    Raises:
        ValueError: If coach or club not found
    """
    # Get coach record from user
    coach = db.query(Coach).filter(Coach.user_id == user_id).first()
    if not coach:
        raise ValueError("Coach not found")

    # Get club record
    club = db.query(Club).filter(Club.coach_id == coach.coach_id).first()
    if not club:
        raise ValueError("Coach has no club")

    return club


def verify_match_ownership(db: Session, match_id: UUID, club_id: UUID) -> Match:
    """
    Verify match belongs to coach's club.

    Args:
        db: Database session
        match_id: Match UUID
        club_id: Club UUID

    Returns:
        Match instance

    Raises:
        ValueError: If match not found or doesn't belong to club
    """
    match = db.query(Match).filter(Match.match_id == match_id).first()

    if not match:
        raise ValueError("Match not found")

    if str(match.club_id) != str(club_id):
        raise ValueError("This match does not belong to your club")

    return match


def verify_player_ownership(db: Session, player_id: UUID, club_id: UUID) -> Player:
    """
    Verify player belongs to coach's club.

    Args:
        db: Database session
        player_id: Player UUID
        club_id: Club UUID

    Returns:
        Player instance

    Raises:
        ValueError: If player not found or doesn't belong to club
    """
    player = db.query(Player).filter(Player.player_id == player_id).first()

    if not player:
        raise ValueError("Player not found")

    if str(player.club_id) != str(club_id):
        raise ValueError("This player does not belong to your club")

    return player


def verify_training_plan_ownership(db: Session, plan_id: UUID, coach_id: UUID) -> TrainingPlan:
    """
    Verify training plan belongs to coach's club (via player).

    Args:
        db: Database session
        plan_id: Training plan UUID
        coach_id: Coach UUID

    Returns:
        TrainingPlan instance

    Raises:
        ValueError: If plan not found or doesn't belong to coach's club
    """
    plan = (
        db.query(TrainingPlan)
        .join(Player, TrainingPlan.player_id == Player.player_id)
        .join(Club, Player.club_id == Club.club_id)
        .filter(
            TrainingPlan.plan_id == plan_id,
            Club.coach_id == coach_id
        )
        .first()
    )

    if not plan:
        raise ValueError("Training plan not found or does not belong to your club")

    return plan


# ============================================================================
# DASHBOARD & PROFILE SERVICES
# ============================================================================

def get_coach_profile(db: Session, user_id: UUID) -> Dict[str, Any]:
    """
    Get coach profile data.

    Args:
        db: Database session
        user_id: User UUID from JWT token

    Returns:
        Dict matching CoachProfileResponse schema

    Raises:
        ValueError: If coach or club not found
    """
    # Get user, coach, and club
    result = (
        db.query(User, Coach, Club)
        .join(Coach, User.user_id == Coach.user_id)
        .join(Club, Coach.coach_id == Club.coach_id)
        .filter(User.user_id == user_id)
        .first()
    )

    if not result:
        raise ValueError("Coach or club not found")

    user, coach, club = result

    # Count linked players
    linked_count = db.query(func.count(Player.player_id)).filter(
        Player.club_id == club.club_id,
        Player.is_linked == True
    ).scalar() or 0

    # Get club season statistics for win rate
    club_stats = db.query(ClubSeasonStatistics).filter(
        ClubSeasonStatistics.club_id == club.club_id
    ).first()

    matches_played = club_stats.matches_played if club_stats else 0
    wins = club_stats.wins if club_stats else 0
    win_rate = _calculate_win_rate(wins, matches_played)

    return {
        "coach": {
            "full_name": user.full_name,
            "email": user.email,
            "gender": coach.gender,
            "birth_date": coach.birth_date
        },
        "club": {
            "club_id": str(club.club_id),
            "club_name": club.club_name,
            "logo_url": club.logo_url
        },
        "club_stats": {
            "total_players": linked_count,
            "total_matches": matches_played,
            "win_rate_percentage": win_rate
        }
    }


def get_dashboard_data(
    db: Session,
    user_id: UUID,
    matches_limit: int = 20,
    matches_offset: int = 0
) -> Dict[str, Any]:
    """
    Get all data for coach dashboard.

    Args:
        db: Database session
        user_id: User UUID from JWT token
        matches_limit: Maximum matches to return
        matches_offset: Offset for pagination

    Returns:
        Dict matching DashboardResponse schema

    Raises:
        ValueError: If coach or club not found
    """
    # Get coach and club
    result = (
        db.query(User, Coach, Club)
        .join(Coach, User.user_id == Coach.user_id)
        .join(Club, Coach.coach_id == Club.coach_id)
        .filter(User.user_id == user_id)
        .first()
    )

    if not result:
        raise ValueError("Coach or club not found")

    user, coach, club = result

    # Get club season statistics
    club_stats = db.query(ClubSeasonStatistics).filter(
        ClubSeasonStatistics.club_id == club.club_id
    ).first()

    # Default values if no stats yet
    if not club_stats:
        return {
            "coach": {"full_name": user.full_name},
            "club": {
                "club_id": str(club.club_id),
                "club_name": club.club_name,
                "logo_url": club.logo_url
            },
            "season_record": {"wins": 0, "draws": 0, "losses": 0},
            "team_form": "",
            "matches": {"total_count": 0, "matches": []},
            "statistics": {
                "season_summary": {
                    "matches_played": 0,
                    "goals_scored": 0,
                    "goals_conceded": 0,
                    "total_assists": 0
                },
                "attacking": {
                    "avg_goals_per_match": None,
                    "avg_xg_per_match": None,
                    "avg_total_shots": None,
                    "avg_shots_on_target": None,
                    "avg_dribbles": None,
                    "avg_successful_dribbles": None
                },
                "passes": {
                    "avg_possession_percentage": None,
                    "avg_passes": None,
                    "pass_completion_percentage": None,
                    "avg_final_third_passes": None,
                    "avg_crosses": None
                },
                "defending": {
                    "total_clean_sheets": 0,
                    "avg_goals_conceded_per_match": None,
                    "avg_tackles": None,
                    "tackle_success_percentage": None,
                    "avg_interceptions": None,
                    "interception_success_percentage": None,
                    "avg_ball_recoveries": None,
                    "avg_saves_per_match": None
                }
            }
        }

    # Get matches with pagination and total count
    matches_query = (
        db.query(
            Match,
            func.count(Match.match_id).over().label('total_count')
        )
        .filter(Match.club_id == club.club_id)
        .order_by(Match.match_date.desc())
        .offset(matches_offset)
        .limit(matches_limit)
    )

    matches_result = matches_query.all()
    total_count = matches_result[0].total_count if matches_result else 0

    matches_list = []
    for match, _ in matches_result:
        matches_list.append({
            "match_id": str(match.match_id),
            "opponent_name": match.opponent_name,
            "match_date": match.match_date,
            "our_score": match.our_score,
            "opponent_score": match.opponent_score,
            "result": match.result
        })

    return {
        "coach": {"full_name": user.full_name},
        "club": {
            "club_id": str(club.club_id),
            "club_name": club.club_name,
            "logo_url": club.logo_url
        },
        "season_record": {
            "wins": club_stats.wins,
            "draws": club_stats.draws,
            "losses": club_stats.losses
        },
        "team_form": club_stats.team_form or "",
        "matches": {
            "total_count": total_count,
            "matches": matches_list
        },
        "statistics": {
            "season_summary": {
                "matches_played": club_stats.matches_played,
                "goals_scored": club_stats.goals_scored,
                "goals_conceded": club_stats.goals_conceded,
                "total_assists": club_stats.total_assists
            },
            "attacking": {
                "avg_goals_per_match": float(club_stats.avg_goals_per_match) if club_stats.avg_goals_per_match else None,
                "avg_xg_per_match": float(club_stats.avg_xg_per_match) if club_stats.avg_xg_per_match else None,
                "avg_total_shots": float(club_stats.avg_total_shots) if club_stats.avg_total_shots else None,
                "avg_shots_on_target": float(club_stats.avg_shots_on_target) if club_stats.avg_shots_on_target else None,
                "avg_dribbles": float(club_stats.avg_dribbles) if club_stats.avg_dribbles else None,
                "avg_successful_dribbles": float(club_stats.avg_successful_dribbles) if club_stats.avg_successful_dribbles else None
            },
            "passes": {
                "avg_possession_percentage": float(club_stats.avg_possession_percentage) if club_stats.avg_possession_percentage else None,
                "avg_passes": float(club_stats.avg_total_passes) if club_stats.avg_total_passes else None,  # Note: maps to avg_total_passes
                "pass_completion_percentage": float(club_stats.pass_completion_rate) if club_stats.pass_completion_rate else None,  # Note: maps to pass_completion_rate
                "avg_final_third_passes": float(club_stats.avg_final_third_passes) if club_stats.avg_final_third_passes else None,
                "avg_crosses": float(club_stats.avg_crosses) if club_stats.avg_crosses else None
            },
            "defending": {
                "total_clean_sheets": club_stats.total_clean_sheets,
                "avg_goals_conceded_per_match": float(club_stats.avg_goals_conceded_per_match) if club_stats.avg_goals_conceded_per_match else None,
                "avg_tackles": float(club_stats.avg_tackles) if club_stats.avg_tackles else None,
                "tackle_success_percentage": float(club_stats.tackle_success_rate) if club_stats.tackle_success_rate else None,  # Note: maps to tackle_success_rate
                "avg_interceptions": float(club_stats.avg_interceptions) if club_stats.avg_interceptions else None,
                "interception_success_percentage": float(club_stats.interception_success_rate) if club_stats.interception_success_rate else None,  # Note: maps to interception_success_rate
                "avg_ball_recoveries": float(club_stats.avg_ball_recoveries) if club_stats.avg_ball_recoveries else None,
                "avg_saves_per_match": float(club_stats.avg_saves_per_match) if club_stats.avg_saves_per_match else None
            }
        }
    }


# ============================================================================
# MATCH SERVICES
# ============================================================================

def get_match_detail(db: Session, match_id: UUID, club_id: UUID) -> Dict[str, Any]:
    """
    Get complete match details.

    Args:
        db: Database session
        match_id: Match UUID
        club_id: Club UUID

    Returns:
        Dict matching MatchDetailResponse schema

    Raises:
        ValueError: If match not found or doesn't belong to club
    """
    # Verify ownership and get match
    match = verify_match_ownership(db, match_id, club_id)

    # Get club
    club = db.query(Club).filter(Club.club_id == club_id).first()

    # Get opponent club
    opponent = db.query(OpponentClub).filter(
        OpponentClub.opponent_club_id == match.opponent_club_id
    ).first()

    # Get goals ordered by minute, second
    goals = (
        db.query(Goal)
        .filter(Goal.match_id == match_id)
        .order_by(Goal.minute.asc(), Goal.second.asc())
        .all()
    )

    goal_scorers = [{
        "goal_id": str(goal.goal_id),
        "scorer_name": goal.scorer_name,
        "minute": goal.minute,
        "second": goal.second,
        "is_our_goal": goal.is_our_goal
    } for goal in goals]

    # Get match statistics for both teams
    our_stats = db.query(MatchStatistics).filter(
        MatchStatistics.match_id == match_id,
        MatchStatistics.team_type == 'our_team'
    ).first()

    opp_stats = db.query(MatchStatistics).filter(
        MatchStatistics.match_id == match_id,
        MatchStatistics.team_type == 'opponent_team'
    ).first()

    # Build statistics comparison
    if our_stats and opp_stats:
        statistics = {
            "match_overview": {
                "ball_possession": _build_stat_comparison(
                    float(our_stats.possession_percentage) if our_stats.possession_percentage else 0,
                    float(opp_stats.possession_percentage) if opp_stats.possession_percentage else 0
                ),
                "expected_goals": _build_stat_comparison(
                    float(our_stats.expected_goals) if our_stats.expected_goals else 0,
                    float(opp_stats.expected_goals) if opp_stats.expected_goals else 0
                ),
                "total_shots": _build_stat_comparison(our_stats.total_shots, opp_stats.total_shots),
                "goalkeeper_saves": _build_stat_comparison(our_stats.goalkeeper_saves, opp_stats.goalkeeper_saves),
                "total_passes": _build_stat_comparison(our_stats.total_passes, opp_stats.total_passes),
                "total_dribbles": _build_stat_comparison(our_stats.total_dribbles, opp_stats.total_dribbles)
            },
            "attacking": {
                "total_shots": _build_stat_comparison(our_stats.total_shots, opp_stats.total_shots),
                "shots_on_target": _build_stat_comparison(our_stats.shots_on_target, opp_stats.shots_on_target),
                "shots_off_target": _build_stat_comparison(our_stats.shots_off_target, opp_stats.shots_off_target),
                "total_dribbles": _build_stat_comparison(our_stats.total_dribbles, opp_stats.total_dribbles),
                "successful_dribbles": _build_stat_comparison(our_stats.successful_dribbles, opp_stats.successful_dribbles)
            },
            "passing": {
                "total_passes": _build_stat_comparison(our_stats.total_passes, opp_stats.total_passes),
                "passes_completed": _build_stat_comparison(our_stats.passes_completed, opp_stats.passes_completed),
                "passes_in_final_third": _build_stat_comparison(our_stats.passes_in_final_third, opp_stats.passes_in_final_third),
                "long_passes": _build_stat_comparison(our_stats.long_passes, opp_stats.long_passes),
                "crosses": _build_stat_comparison(our_stats.crosses, opp_stats.crosses)
            },
            "defending": {
                "tackle_success_percentage": _build_stat_comparison(
                    float(our_stats.tackle_success_percentage) if our_stats.tackle_success_percentage else 0,
                    float(opp_stats.tackle_success_percentage) if opp_stats.tackle_success_percentage else 0
                ),
                "total_tackles": _build_stat_comparison(our_stats.total_tackles, opp_stats.total_tackles),
                "interceptions": _build_stat_comparison(our_stats.interceptions, opp_stats.interceptions),
                "ball_recoveries": _build_stat_comparison(our_stats.ball_recoveries, opp_stats.ball_recoveries),
                "goalkeeper_saves": _build_stat_comparison(our_stats.goalkeeper_saves, opp_stats.goalkeeper_saves)
            }
        }
    else:
        # Return zeros if no statistics
        statistics = {
            "match_overview": {
                "ball_possession": _build_stat_comparison(0, 0),
                "expected_goals": _build_stat_comparison(0, 0),
                "total_shots": _build_stat_comparison(0, 0),
                "goalkeeper_saves": _build_stat_comparison(0, 0),
                "total_passes": _build_stat_comparison(0, 0),
                "total_dribbles": _build_stat_comparison(0, 0)
            },
            "attacking": {
                "total_shots": _build_stat_comparison(0, 0),
                "shots_on_target": _build_stat_comparison(0, 0),
                "shots_off_target": _build_stat_comparison(0, 0),
                "total_dribbles": _build_stat_comparison(0, 0),
                "successful_dribbles": _build_stat_comparison(0, 0)
            },
            "passing": {
                "total_passes": _build_stat_comparison(0, 0),
                "passes_completed": _build_stat_comparison(0, 0),
                "passes_in_final_third": _build_stat_comparison(0, 0),
                "long_passes": _build_stat_comparison(0, 0),
                "crosses": _build_stat_comparison(0, 0)
            },
            "defending": {
                "tackle_success_percentage": _build_stat_comparison(0, 0),
                "total_tackles": _build_stat_comparison(0, 0),
                "interceptions": _build_stat_comparison(0, 0),
                "ball_recoveries": _build_stat_comparison(0, 0),
                "goalkeeper_saves": _build_stat_comparison(0, 0)
            }
        }

    # Get lineups for both teams
    our_lineup = (
        db.query(MatchLineup)
        .filter(
            MatchLineup.match_id == match_id,
            MatchLineup.team_type == 'our_team'
        )
        .all()
    )

    opp_lineup = (
        db.query(MatchLineup)
        .filter(
            MatchLineup.match_id == match_id,
            MatchLineup.team_type == 'opponent_team'
        )
        .all()
    )

    our_team_players = [{
        "player_id": str(lineup.player_id),
        "jersey_number": lineup.jersey_number,
        "player_name": lineup.player_name,
        "position": lineup.position
    } for lineup in our_lineup]

    opponent_team_players = [{
        "opponent_player_id": str(lineup.opponent_player_id),
        "jersey_number": lineup.jersey_number,
        "player_name": lineup.player_name,
        "position": lineup.position
    } for lineup in opp_lineup]

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
                "logo_url": opponent.logo_url if opponent else None
            }
        },
        "summary": {
            "goal_scorers": goal_scorers
        },
        "statistics": statistics,
        "lineup": {
            "our_team": our_team_players,
            "opponent_team": opponent_team_players
        }
    }


# ============================================================================
# PLAYER SERVICES
# ============================================================================

def get_players_list(db: Session, club_id: UUID) -> Dict[str, Any]:
    """
    Get all players in club with summary counts.

    Args:
        db: Database session
        club_id: Club UUID

    Returns:
        Dict matching PlayersListResponse schema
    """
    # Get summary counts
    total_players = db.query(func.count(Player.player_id)).filter(
        Player.club_id == club_id
    ).scalar() or 0

    joined_count = db.query(func.count(Player.player_id)).filter(
        Player.club_id == club_id,
        Player.is_linked == True
    ).scalar() or 0

    pending_count = db.query(func.count(Player.player_id)).filter(
        Player.club_id == club_id,
        Player.is_linked == False
    ).scalar() or 0

    # Get all players ordered by jersey number
    players = (
        db.query(Player)
        .filter(Player.club_id == club_id)
        .order_by(Player.jersey_number.asc())
        .all()
    )

    players_list = [{
        "player_id": str(player.player_id),
        "player_name": player.player_name,
        "jersey_number": player.jersey_number,
        "profile_image_url": player.profile_image_url,
        "is_linked": player.is_linked
    } for player in players]

    return {
        "summary": {
            "total_players": total_players,
            "joined": joined_count,
            "pending": pending_count
        },
        "players": players_list
    }


def get_player_detail(
    db: Session,
    player_id: UUID,
    club_id: UUID,
    matches_limit: int = 20,
    matches_offset: int = 0
) -> Dict[str, Any]:
    """
    Get complete player details.

    Args:
        db: Database session
        player_id: Player UUID
        club_id: Club UUID
        matches_limit: Maximum matches to return
        matches_offset: Offset for pagination

    Returns:
        Dict matching PlayerDetailResponse schema

    Raises:
        ValueError: If player not found or doesn't belong to club
    """
    # Verify ownership and get player
    player = verify_player_ownership(db, player_id, club_id)

    # Get player season statistics
    season_stats = db.query(PlayerSeasonStatistics).filter(
        PlayerSeasonStatistics.player_id == player_id
    ).first()

    # Calculate age
    age_str = calculate_age(player.birth_date)

    # Get player's matches with pagination
    matches_query = (
        db.query(
            Match,
            func.count(Match.match_id).over().label('total_count')
        )
        .join(PlayerMatchStatistics, Match.match_id == PlayerMatchStatistics.match_id)
        .filter(PlayerMatchStatistics.player_id == player_id)
        .order_by(Match.match_date.desc())
        .offset(matches_offset)
        .limit(matches_limit)
    )

    matches_result = matches_query.all()
    total_count = matches_result[0].total_count if matches_result else 0

    matches_list = []
    for match, _ in matches_result:
        matches_list.append({
            "match_id": str(match.match_id),
            "opponent_name": match.opponent_name,
            "match_date": match.match_date,
            "our_score": match.our_score,
            "opponent_score": match.opponent_score,
            "result": match.result
        })

    # Get training plans
    training_plans = (
        db.query(TrainingPlan)
        .filter(TrainingPlan.player_id == player_id)
        .order_by(TrainingPlan.created_at.desc())
        .all()
    )

    training_plans_list = [{
        "plan_id": str(plan.plan_id),
        "plan_name": plan.plan_name,
        "created_at": plan.created_at.date() if isinstance(plan.created_at, datetime) else plan.created_at,
        "status": plan.status
    } for plan in training_plans]

    # Build response
    if season_stats:
        attributes = {
            "attacking_rating": season_stats.attacking_rating,
            "technique_rating": season_stats.technique_rating,
            "creativity_rating": season_stats.creativity_rating,
            "tactical_rating": season_stats.tactical_rating,
            "defending_rating": season_stats.defending_rating
        }
        season_statistics = {
            "general": {
                "matches_played": season_stats.matches_played
            },
            "attacking": {
                "goals": season_stats.goals,
                "assists": season_stats.assists,
                "expected_goals": float(season_stats.expected_goals) if season_stats.expected_goals else None,
                "shots_per_game": float(season_stats.shots_per_game) if season_stats.shots_per_game else None,
                "shots_on_target_per_game": float(season_stats.shots_on_target_per_game) if season_stats.shots_on_target_per_game else None
            },
            "passing": {
                "total_passes": season_stats.total_passes,
                "passes_completed": season_stats.passes_completed
            },
            "dribbling": {
                "total_dribbles": season_stats.total_dribbles,
                "successful_dribbles": season_stats.successful_dribbles
            },
            "defending": {
                "tackles": season_stats.tackles,
                "tackle_success_rate": float(season_stats.tackle_success_rate) if season_stats.tackle_success_rate else None,
                "interceptions": season_stats.interceptions,
                "interception_success_rate": float(season_stats.interception_success_rate) if season_stats.interception_success_rate else None
            }
        }
    else:
        attributes = {
            "attacking_rating": None,
            "technique_rating": None,
            "creativity_rating": None,
            "tactical_rating": None,
            "defending_rating": None
        }
        season_statistics = {
            "general": {"matches_played": 0},
            "attacking": {
                "goals": 0,
                "assists": 0,
                "expected_goals": None,
                "shots_per_game": None,
                "shots_on_target_per_game": None
            },
            "passing": {
                "total_passes": None,
                "passes_completed": None
            },
            "dribbling": {
                "total_dribbles": None,
                "successful_dribbles": None
            },
            "defending": {
                "tackles": None,
                "tackle_success_rate": None,
                "interceptions": None,
                "interception_success_rate": None
            }
        }

    return {
        "player": {
            "player_id": str(player.player_id),
            "player_name": player.player_name,
            "jersey_number": player.jersey_number,
            "height": player.height,
            "age": age_str,
            "profile_image_url": player.profile_image_url,
            "is_linked": player.is_linked
        },
        "invite_code": player.invite_code if not player.is_linked else None,
        "attributes": attributes,
        "season_statistics": season_statistics,
        "matches": {
            "total_count": total_count,
            "matches": matches_list
        },
        "training_plans": training_plans_list
    }


def get_player_match_stats(
    db: Session,
    player_id: UUID,
    match_id: UUID,
    club_id: UUID
) -> Dict[str, Any]:
    """
    Get player's performance in specific match.

    Args:
        db: Database session
        player_id: Player UUID
        match_id: Match UUID
        club_id: Club UUID

    Returns:
        Dict matching PlayerMatchDetailResponse schema

    Raises:
        ValueError: If player/match not found or don't belong to club
    """
    # Verify ownership
    player = verify_player_ownership(db, player_id, club_id)
    match = verify_match_ownership(db, match_id, club_id)

    # Get club and opponent
    club = db.query(Club).filter(Club.club_id == club_id).first()
    opponent = db.query(OpponentClub).filter(
        OpponentClub.opponent_club_id == match.opponent_club_id
    ).first()

    # Get player match statistics
    player_stats = db.query(PlayerMatchStatistics).filter(
        PlayerMatchStatistics.player_id == player_id,
        PlayerMatchStatistics.match_id == match_id
    ).first()

    if not player_stats:
        raise ValueError("Player statistics not found for this match")

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
                "logo_url": opponent.logo_url if opponent else None
            }
        },
        "player_summary": {
            "player_name": player.player_name,
            "goals": player_stats.goals,
            "assists": player_stats.assists
        },
        "statistics": {
            "attacking": {
                "goals": player_stats.goals,
                "assists": player_stats.assists,
                "xg": float(player_stats.expected_goals) if player_stats.expected_goals else None,
                "total_shots": player_stats.shots,
                "shots_on_target": player_stats.shots_on_target,
                "total_dribbles": player_stats.total_dribbles,
                "successful_dribbles": player_stats.successful_dribbles
            },
            "passing": {
                "total_passes": player_stats.total_passes,
                "passes_completed": player_stats.completed_passes,
                "short_passes": player_stats.short_passes,
                "long_passes": player_stats.long_passes,
                "final_third": player_stats.final_third_passes,
                "crosses": player_stats.crosses
            },
            "defending": {
                "tackles": player_stats.tackles,
                "tackle_success_rate": float(player_stats.tackle_success_rate) if player_stats.tackle_success_rate else None,
                "interceptions": player_stats.interceptions,
                "interception_success_rate": float(player_stats.interception_success_rate) if player_stats.interception_success_rate else None
            }
        }
    }


# ============================================================================
# TRAINING PLAN SERVICES
# ============================================================================

def generate_ai_training_plan(
    db: Session,
    player_id: UUID,
    club_id: UUID
) -> Dict[str, Any]:
    """
    Generate AI training plan (stub implementation).

    Args:
        db: Database session
        player_id: Player UUID
        club_id: Club UUID

    Returns:
        Dict matching GenerateAITrainingPlanResponse schema

    Raises:
        ValueError: If player not found or doesn't belong to club
    """
    # Verify ownership
    player = verify_player_ownership(db, player_id, club_id)

    # Stub implementation - return hardcoded example
    return {
        "player_name": player.player_name,
        "jersey_number": player.jersey_number,
        "plan_name": f"AI-Generated Plan for {player.player_name}",
        "duration": "2 weeks",
        "exercises": [
            {
                "exercise_name": "Dribbling Drills",
                "description": "Practice ball control and close dribbling",
                "sets": "3",
                "reps": "10",
                "duration_minutes": "15"
            },
            {
                "exercise_name": "Shooting Practice",
                "description": "Accuracy and power shooting exercises",
                "sets": "4",
                "reps": "8",
                "duration_minutes": "20"
            },
            {
                "exercise_name": "Passing Combinations",
                "description": "Short and long passing drills with teammates",
                "sets": "3",
                "reps": "12",
                "duration_minutes": "15"
            }
        ]
    }


def create_training_plan(
    db: Session,
    player_id: UUID,
    coach_id: UUID,
    plan_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create new training plan with exercises.

    Args:
        db: Database session
        player_id: Player UUID
        coach_id: Coach UUID
        plan_data: Plan data from request

    Returns:
        Dict matching CreateTrainingPlanResponse schema

    Raises:
        ValueError: If player not found or doesn't belong to coach's club
    """
    # Verify player belongs to coach's club
    coach_club = (
        db.query(Club)
        .filter(Club.coach_id == coach_id)
        .first()
    )

    if not coach_club:
        raise ValueError("Coach has no club")

    player = verify_player_ownership(db, player_id, coach_club.club_id)

    # Create training plan
    plan = TrainingPlan(
        player_id=player_id,
        created_by=coach_id,
        plan_name=plan_data["plan_name"],
        duration=plan_data.get("duration"),
        coach_notes=plan_data.get("coach_notes"),
        status="pending"
    )

    db.add(plan)
    db.flush()
    db.refresh(plan)

    # Create exercises
    exercises_data = plan_data.get("exercises", [])
    for exercise_data in exercises_data:
        exercise = TrainingExercise(
            plan_id=plan.plan_id,
            exercise_name=exercise_data["exercise_name"],
            description=exercise_data.get("description"),
            sets=exercise_data.get("sets"),
            reps=exercise_data.get("reps"),
            duration_minutes=exercise_data.get("duration_minutes"),
            exercise_order=exercise_data["exercise_order"],
            completed=False
        )
        db.add(exercise)

    db.flush()

    return {
        "plan_id": str(plan.plan_id),
        "player_id": str(plan.player_id),
        "plan_name": plan.plan_name,
        "duration": plan.duration,
        "status": plan.status,
        "coach_notes": plan.coach_notes,
        "exercise_count": len(exercises_data),
        "created_at": plan.created_at
    }


def get_training_plan_detail(
    db: Session,
    plan_id: UUID,
    coach_id: UUID
) -> Dict[str, Any]:
    """
    Get training plan details.

    Args:
        db: Database session
        plan_id: Training plan UUID
        coach_id: Coach UUID

    Returns:
        Dict matching TrainingPlanDetailResponse schema

    Raises:
        ValueError: If plan not found or doesn't belong to coach's club
    """
    # Verify ownership
    plan = verify_training_plan_ownership(db, plan_id, coach_id)

    # Get player
    player = db.query(Player).filter(Player.player_id == plan.player_id).first()

    # Get exercises
    exercises = (
        db.query(TrainingExercise)
        .filter(TrainingExercise.plan_id == plan_id)
        .order_by(TrainingExercise.exercise_order.asc())
        .all()
    )

    # Calculate progress
    progress = _calculate_training_progress(exercises)

    exercises_list = [{
        "exercise_id": str(ex.exercise_id),
        "exercise_name": ex.exercise_name,
        "description": ex.description,
        "sets": ex.sets,
        "reps": ex.reps,
        "duration_minutes": ex.duration_minutes,
        "completed": ex.completed,
        "exercise_order": ex.exercise_order
    } for ex in exercises]

    return {
        "plan": {
            "plan_id": str(plan.plan_id),
            "plan_name": plan.plan_name,
            "player_name": player.player_name,
            "player_jersey": player.jersey_number,
            "status": plan.status,
            "created_at": plan.created_at.date() if isinstance(plan.created_at, datetime) else plan.created_at
        },
        "progress": progress,
        "exercises": exercises_list,
        "coach_notes": plan.coach_notes
    }


def update_training_plan(
    db: Session,
    plan_id: UUID,
    coach_id: UUID,
    update_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update training plan and exercises.

    Args:
        db: Database session
        plan_id: Training plan UUID
        coach_id: Coach UUID
        update_data: Update data from request

    Returns:
        Dict matching UpdateTrainingPlanResponse schema

    Raises:
        ValueError: If plan not found or doesn't belong to coach's club
    """
    # Verify ownership
    plan = verify_training_plan_ownership(db, plan_id, coach_id)

    # Update plan fields
    if "plan_name" in update_data and update_data["plan_name"] is not None:
        plan.plan_name = update_data["plan_name"]

    if "duration" in update_data and update_data["duration"] is not None:
        plan.duration = update_data["duration"]

    if "coach_notes" in update_data and update_data["coach_notes"] is not None:
        plan.coach_notes = update_data["coach_notes"]

    # Update exercises if provided
    if "exercises" in update_data and update_data["exercises"] is not None:
        exercises_data = update_data["exercises"]

        # Get existing exercises
        existing_exercises = (
            db.query(TrainingExercise)
            .filter(TrainingExercise.plan_id == plan_id)
            .all()
        )

        # Build map of existing exercises by ID
        existing_map = {str(ex.exercise_id): ex for ex in existing_exercises}
        updated_ids = set()

        # Process updates
        for exercise_data in exercises_data:
            exercise_id = exercise_data.get("exercise_id")

            if exercise_id and exercise_id in existing_map:
                # Update existing exercise
                exercise = existing_map[exercise_id]
                exercise.exercise_name = exercise_data["exercise_name"]
                exercise.description = exercise_data.get("description")
                exercise.sets = exercise_data.get("sets")
                exercise.reps = exercise_data.get("reps")
                exercise.duration_minutes = exercise_data.get("duration_minutes")
                exercise.exercise_order = exercise_data["exercise_order"]
                updated_ids.add(exercise_id)
            else:
                # Create new exercise
                new_exercise = TrainingExercise(
                    plan_id=plan_id,
                    exercise_name=exercise_data["exercise_name"],
                    description=exercise_data.get("description"),
                    sets=exercise_data.get("sets"),
                    reps=exercise_data.get("reps"),
                    duration_minutes=exercise_data.get("duration_minutes"),
                    exercise_order=exercise_data["exercise_order"],
                    completed=False
                )
                db.add(new_exercise)

        # Delete exercises not in update list
        for exercise_id, exercise in existing_map.items():
            if exercise_id not in updated_ids:
                db.delete(exercise)

    db.flush()

    return {
        "plan_id": str(plan.plan_id),
        "player_id": str(plan.player_id),
        "plan_name": plan.plan_name,
        "duration": plan.duration,
        "status": plan.status,
        "updated": True
    }


def delete_training_plan(
    db: Session,
    plan_id: UUID,
    coach_id: UUID
) -> Dict[str, Any]:
    """
    Delete training plan (cascades to exercises).

    Args:
        db: Database session
        plan_id: Training plan UUID
        coach_id: Coach UUID

    Returns:
        Dict matching DeleteTrainingPlanResponse schema

    Raises:
        ValueError: If plan not found or doesn't belong to coach's club
    """
    # Verify ownership
    plan = verify_training_plan_ownership(db, plan_id, coach_id)

    # Delete plan (cascade deletes exercises)
    db.delete(plan)
    db.flush()

    return {
        "deleted": True,
        "plan_id": str(plan_id)
    }
