"""
Match Analysis Query Tools

Synchronous database query tools for match-related chatbot queries.
"""

from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from uuid import UUID

from app.models import Match, MatchStatistics, Goal


def get_last_match(
    db: Session,
    club_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Get the most recent match for a club.

    Args:
        db: Database session
        club_id: Club ID

    Returns:
        Match information
    """
    query = (
        select(Match)
        .where(Match.club_id == str(club_id))
        .order_by(Match.match_date.desc())
        .limit(1)
    )

    result = db.execute(query)
    match = result.scalar_one_or_none()

    if not match:
        return None

    return {
        "match_id": str(match.match_id),
        "date": match.match_date.strftime("%Y-%m-%d"),
        "opponent": match.opponent_name,
        "score": f"{match.our_score}-{match.opponent_score}",
        "result": match.result
    }


def get_match_details(
    db: Session,
    club_id: UUID,
    match_description: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a match.

    Args:
        db: Database session
        club_id: Club ID
        match_description: Match description (e.g., "last match", "vs Team X")

    Returns:
        Match details
    """
    # If no description or "last match", get most recent
    if not match_description or match_description.lower() in ["last match", "latest match", "most recent"]:
        return get_last_match(db, club_id)

    # Search by opponent name (fuzzy match)
    # Extract opponent name from "vs Team X" or just "Team X"
    opponent_search = match_description.lower().replace("vs ", "").replace("against ", "").strip()

    query = (
        select(Match)
        .where(
            and_(
                Match.club_id == str(club_id),
                Match.opponent_name.ilike(f"%{opponent_search}%")
            )
        )
        .order_by(Match.match_date.desc())
        .limit(1)
    )

    result = db.execute(query)
    match = result.scalar_one_or_none()

    if not match:
        # If no match found, return last match as fallback
        return get_last_match(db, club_id)

    return {
        "match_id": str(match.match_id),
        "date": match.match_date.strftime("%Y-%m-%d"),
        "opponent": match.opponent_name,
        "score": f"{match.our_score}-{match.opponent_score}",
        "result": match.result
    }


def get_match_statistics(
    db: Session,
    club_id: UUID,
    match_description: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get statistics for a match (both teams).

    Args:
        db: Database session
        club_id: Club ID
        match_description: Match description

    Returns:
        Match statistics for both teams
    """
    # Get the match
    match_info = get_match_details(db, club_id, match_description)
    if not match_info:
        return {"error": "Match not found"}

    match_id = UUID(match_info["match_id"])

    # Get statistics for both teams
    query = select(MatchStatistics).where(MatchStatistics.match_id == str(match_id))
    result = db.execute(query)
    stats_list = result.scalars().all()

    our_stats = None
    opponent_stats = None

    for stats in stats_list:
        if stats.team_type == 'our_team':
            our_stats = stats
        else:
            opponent_stats = stats

    response = {
        "match_date": match_info["date"],
        "opponent": match_info["opponent"],
        "score": match_info["score"],
        "result": match_info["result"]
    }

    if our_stats:
        response["our_team"] = {
            "possession": round(float(our_stats.possession_percentage), 1) if our_stats.possession_percentage else 0,
            "expected_goals": round(float(our_stats.expected_goals), 2) if our_stats.expected_goals else 0,
            "total_shots": our_stats.total_shots or 0,
            "shots_on_target": our_stats.shots_on_target or 0,
            "shots_off_target": our_stats.shots_off_target or 0,
            "goalkeeper_saves": our_stats.goalkeeper_saves or 0,
            "total_passes": our_stats.total_passes or 0,
            "passes_completed": our_stats.passes_completed or 0,
            "pass_completion_rate": round(float(our_stats.pass_completion_rate), 1) if our_stats.pass_completion_rate else 0,
            "passes_in_final_third": our_stats.passes_in_final_third or 0,
            "long_passes": our_stats.long_passes or 0,
            "crosses": our_stats.crosses or 0,
            "total_dribbles": our_stats.total_dribbles or 0,
            "successful_dribbles": our_stats.successful_dribbles or 0,
            "total_tackles": our_stats.total_tackles or 0,
            "tackle_success_percentage": round(float(our_stats.tackle_success_percentage), 1) if our_stats.tackle_success_percentage else 0,
            "interceptions": our_stats.interceptions or 0,
            "ball_recoveries": our_stats.ball_recoveries or 0
        }

    if opponent_stats:
        response["opponent_team"] = {
            "possession": round(float(opponent_stats.possession_percentage), 1) if opponent_stats.possession_percentage else 0,
            "expected_goals": round(float(opponent_stats.expected_goals), 2) if opponent_stats.expected_goals else 0,
            "total_shots": opponent_stats.total_shots or 0,
            "shots_on_target": opponent_stats.shots_on_target or 0,
            "total_passes": opponent_stats.total_passes or 0,
            "pass_completion_rate": round(float(opponent_stats.pass_completion_rate), 1) if opponent_stats.pass_completion_rate else 0,
            "total_tackles": opponent_stats.total_tackles or 0,
            "interceptions": opponent_stats.interceptions or 0
        }

    return response


def get_match_goals_timeline(
    db: Session,
    club_id: UUID,
    match_description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get timeline of goals scored in a match.

    Args:
        db: Database session
        club_id: Club ID
        match_description: Match description (e.g., "last match", "vs Team X")

    Returns:
        Goals timeline with scorers
    """
    # Get the match
    match_info = get_match_details(db, club_id, match_description)
    if not match_info:
        return {"error": "Match not found"}

    match_id = UUID(match_info["match_id"])

    # Get all goals ordered by time
    query = (
        select(Goal)
        .where(Goal.match_id == str(match_id))
        .order_by(Goal.minute, Goal.second)
    )

    result = db.execute(query)
    goals = result.scalars().all()

    return {
        "match_date": match_info["date"],
        "opponent": match_info["opponent"],
        "final_score": match_info["score"],
        "goals": [
            {
                "minute": goal.minute or 0,
                "second": goal.second or 0,
                "scorer": goal.scorer_name,
                "is_our_goal": goal.is_our_goal,
                "team": "Our Team" if goal.is_our_goal else match_info["opponent"]
            }
            for goal in goals
        ],
        "total_goals": len(goals)
    }
