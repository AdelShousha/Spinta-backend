"""
Team Information Query Tools

Synchronous database query tools for team-related chatbot queries.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from uuid import UUID

from app.models import Club, ClubSeasonStatistics, Player


def get_club_season_stats(
    db: Session,
    club_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Get season statistics for a club.

    Args:
        db: Database session
        club_id: Club ID

    Returns:
        Club season statistics
    """
    # Get club info
    club_query = select(Club).where(Club.club_id == str(club_id))
    club_result = db.execute(club_query)
    club = club_result.scalar_one_or_none()

    if not club:
        return {"error": "Club not found"}

    # Get season statistics
    stats_query = select(ClubSeasonStatistics).where(
        ClubSeasonStatistics.club_id == str(club_id)
    )
    stats_result = db.execute(stats_query)
    stats = stats_result.scalar_one_or_none()

    if not stats:
        return {
            "club_name": club.club_name,
            "error": "No statistics found"
        }

    win_rate = (stats.wins / stats.matches_played * 100) if stats.matches_played > 0 else 0
    goal_difference = stats.goals_scored - stats.goals_conceded

    return {
        "club_name": club.club_name,
        "age_group": club.age_group.value if club.age_group else None,
        "matches_played": stats.matches_played,
        "wins": stats.wins,
        "draws": stats.draws,
        "losses": stats.losses,
        "win_rate": round(win_rate, 1),
        "goals_scored": stats.goals_scored,
        "goals_conceded": stats.goals_conceded,
        "goal_difference": goal_difference,
        "total_assists": stats.total_assists or 0,
        "clean_sheets": stats.total_clean_sheets or 0,
        "team_form": stats.team_form,
        "averages": {
            "goals_per_match": round(float(stats.avg_goals_per_match), 2) if stats.avg_goals_per_match else 0,
            "possession": round(float(stats.avg_possession_percentage), 1) if stats.avg_possession_percentage else 0,
            "expected_goals": round(float(stats.avg_xg_per_match), 2) if stats.avg_xg_per_match else 0,
            "shots": round(float(stats.avg_total_shots), 1) if stats.avg_total_shots else 0,
            "shots_on_target": round(float(stats.avg_shots_on_target), 1) if stats.avg_shots_on_target else 0,
            "pass_completion_rate": round(float(stats.pass_completion_rate), 1) if stats.pass_completion_rate else 0,
            "tackles": round(float(stats.avg_tackles), 1) if stats.avg_tackles else 0,
            "tackle_success_rate": round(float(stats.tackle_success_rate), 1) if stats.tackle_success_rate else 0
        }
    }


def get_squad_list(
    db: Session,
    club_id: UUID,
    position_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get list of all players in the squad.

    Args:
        db: Database session
        club_id: Club ID
        position_filter: Filter by position (optional)

    Returns:
        Squad list with player information
    """
    # Get club info
    club_query = select(Club).where(Club.club_id == str(club_id))
    club_result = db.execute(club_query)
    club = club_result.scalar_one_or_none()

    if not club:
        return {"error": "Club not found"}

    # Get players
    players_query = select(Player).where(Player.club_id == str(club_id))

    if position_filter:
        players_query = players_query.where(Player.position.ilike(f"%{position_filter}%"))

    players_query = players_query.order_by(Player.jersey_number)

    players_result = db.execute(players_query)
    players = players_result.scalars().all()

    return {
        "club_name": club.club_name,
        "total_players": len(players),
        "position_filter": position_filter,
        "players": [
            {
                "name": player.player_name,
                "jersey_number": player.jersey_number,
                "position": player.position,
                "height": player.height,
                "profile_image": player.profile_image_url
            }
            for player in players
        ]
    }
