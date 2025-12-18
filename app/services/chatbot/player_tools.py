"""
Player Statistics Query Tools

Synchronous database query tools for player-related chatbot queries.
"""

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.models import Player, PlayerSeasonStatistics


def find_player_by_name(
    db: Session,
    player_name: str,
    club_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Find a player by name (supports fuzzy matching).

    Args:
        db: Database session
        player_name: Player name or partial name
        club_id: Club ID to filter players

    Returns:
        Player information or None if not found
    """
    query = select(Player).where(
        Player.club_id == str(club_id),
        func.lower(Player.player_name).like(f"%{player_name.lower()}%")
    )
    result = db.execute(query)
    player = result.scalar_one_or_none()

    if not player:
        return None

    return {
        "player_id": str(player.player_id),
        "name": player.player_name,
        "position": player.position,
        "jersey_number": player.jersey_number
    }


def get_player_season_stats(
    db: Session,
    player_name: str,
    club_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Get season statistics for a specific player.

    Args:
        db: Database session
        player_name: Player name
        club_id: Club ID

    Returns:
        Player season statistics
    """
    # First find the player
    player_info = find_player_by_name(db, player_name, club_id)
    if not player_info:
        return {"error": f"Player '{player_name}' not found"}

    player_id = UUID(player_info["player_id"])

    # Get season statistics
    query = select(PlayerSeasonStatistics).where(
        PlayerSeasonStatistics.player_id == str(player_id)
    )
    result = db.execute(query)
    stats = result.scalar_one_or_none()

    if not stats:
        return {
            "player_name": player_info["name"],
            "error": "No statistics found"
        }

    return {
        "player_name": player_info["name"],
        "position": player_info["position"],
        "jersey_number": player_info["jersey_number"],
        "matches_played": stats.matches_played,
        "goals": stats.goals,
        "assists": stats.assists,
        "expected_goals": round(float(stats.expected_goals), 2) if stats.expected_goals else 0,
        "shots_per_game": round(float(stats.shots_per_game), 2) if stats.shots_per_game else 0,
        "shots_on_target_per_game": round(float(stats.shots_on_target_per_game), 2) if stats.shots_on_target_per_game else 0,
        "total_passes": stats.total_passes or 0,
        "passes_completed": stats.passes_completed or 0,
        "total_dribbles": stats.total_dribbles or 0,
        "successful_dribbles": stats.successful_dribbles or 0,
        "tackles": stats.tackles or 0,
        "tackle_success_rate": round(float(stats.tackle_success_rate), 1) if stats.tackle_success_rate else 0,
        "interceptions": stats.interceptions or 0,
        "interception_success_rate": round(float(stats.interception_success_rate), 1) if stats.interception_success_rate else 0,
        "attributes": {
            "attacking": stats.attacking_rating,
            "technique": stats.technique_rating,
            "tactical": stats.tactical_rating,
            "defending": stats.defending_rating,
            "creativity": stats.creativity_rating
        }
    }


def get_top_scorers(
    db: Session,
    club_id: UUID,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Get top scorers for a club.

    Args:
        db: Database session
        club_id: Club ID
        limit: Number of players to return (default: 5)

    Returns:
        List of top scorers with statistics
    """
    query = (
        select(Player, PlayerSeasonStatistics)
        .join(PlayerSeasonStatistics, Player.player_id == PlayerSeasonStatistics.player_id)
        .where(
            Player.club_id == str(club_id),
            PlayerSeasonStatistics.goals > 0
        )
        .order_by(PlayerSeasonStatistics.goals.desc())
        .limit(limit)
    )

    result = db.execute(query)
    rows = result.all()

    return [
        {
            "rank": idx + 1,
            "player_name": player.player_name,
            "position": player.position,
            "jersey_number": player.jersey_number,
            "goals": stats.goals,
            "assists": stats.assists,
            "matches_played": stats.matches_played,
            "goals_per_match": round(stats.goals / stats.matches_played, 2) if stats.matches_played > 0 else 0
        }
        for idx, (player, stats) in enumerate(rows)
    ]


def get_top_assisters(
    db: Session,
    club_id: UUID,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Get top assist providers for a club.

    Args:
        db: Database session
        club_id: Club ID
        limit: Number of players to return

    Returns:
        List of top assist providers
    """
    query = (
        select(Player, PlayerSeasonStatistics)
        .join(PlayerSeasonStatistics, Player.player_id == PlayerSeasonStatistics.player_id)
        .where(Player.club_id == str(club_id))
        .order_by(PlayerSeasonStatistics.assists.desc())
        .limit(limit)
    )

    result = db.execute(query)
    rows = result.all()

    if not rows:
        return []

    return [
        {
            "player_name": player.player_name,
            "position": player.position,
            "assists": stats.assists,
            "goals": stats.goals,
            "matches_played": stats.matches_played,
            "assists_per_match": round(stats.assists / stats.matches_played, 2) if stats.matches_played > 0 else 0
        }
        for player, stats in rows
    ]


def compare_players(
    db: Session,
    player1_name: str,
    player2_name: str,
    club_id: UUID
) -> Dict[str, Any]:
    """
    Compare statistics between two players.

    Args:
        db: Database session
        player1_name: First player name
        player2_name: Second player name
        club_id: Club ID

    Returns:
        Side-by-side player comparison
    """
    # Get stats for both players
    player1_stats = get_player_season_stats(db, player1_name, club_id)
    player2_stats = get_player_season_stats(db, player2_name, club_id)

    if "error" in player1_stats:
        return player1_stats
    if "error" in player2_stats:
        return player2_stats

    # Calculate differences
    comparison = {
        "player1": player1_stats,
        "player2": player2_stats,
        "differences": {
            "goals": player1_stats["goals"] - player2_stats["goals"],
            "assists": player1_stats["assists"] - player2_stats["assists"],
            "tackles": player1_stats["tackles"] - player2_stats["tackles"],
            "interceptions": player1_stats["interceptions"] - player2_stats["interceptions"]
        },
        "summary": f"{player1_stats['player_name']} vs {player2_stats['player_name']}"
    }

    return comparison
