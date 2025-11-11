"""
CRUD operations for Goal model.

Functions:
- create_goal: Create new goal record
- get_goals_by_match: Get all goals for a match
"""

from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.goal import Goal


def create_goal(
    db: Session,
    match_id: str,
    team_name: str,
    scorer_name: str,
    minute: int,
    period: int,
    assist_name: Optional[str] = None,
    second: Optional[int] = None,
    goal_type: Optional[str] = None,
    body_part: Optional[str] = None
) -> Goal:
    """
    Create a new goal record.

    Args:
        db: Database session
        match_id: UUID of the match
        team_name: Name of the team that scored
        scorer_name: Name of the player who scored
        minute: Minute of the goal
        period: Match period (1=first half, 2=second half, etc.)
        assist_name: Optional name of player who assisted
        second: Optional second within the minute
        goal_type: Optional goal type (e.g., 'open_play', 'penalty')
        body_part: Optional body part used (e.g., 'right_foot', 'head')

    Returns:
        Created Goal instance

    Example:
        >>> goal = create_goal(
        ...     db,
        ...     match_id="550e8400-...",
        ...     team_name="Manchester United",
        ...     scorer_name="Cristiano Ronaldo",
        ...     minute=25,
        ...     period=1,
        ...     assist_name="Bruno Fernandes",
        ...     goal_type="open_play",
        ...     body_part="right_foot"
        ... )
    """
    goal = Goal(
        match_id=match_id,
        team_name=team_name,
        scorer_name=scorer_name,
        assist_name=assist_name,
        minute=minute,
        second=second,
        period=period,
        goal_type=goal_type,
        body_part=body_part,
        created_at=datetime.now(timezone.utc)
    )

    db.add(goal)
    db.flush()
    db.refresh(goal)

    return goal


def get_goals_by_match(db: Session, match_id: str) -> List[Goal]:
    """
    Get all goals for a specific match.

    Args:
        db: Database session
        match_id: Match UUID

    Returns:
        List of Goal instances ordered by period and minute

    Example:
        >>> goals = get_goals_by_match(db, "550e8400-...")
        >>> for goal in goals:
        ...     print(f"{goal.minute}' - {goal.scorer_name} ({goal.team_name})")
    """
    return db.query(Goal).filter(
        Goal.match_id == match_id
    ).order_by(Goal.period, Goal.minute, Goal.second).all()
