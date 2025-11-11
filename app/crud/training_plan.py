"""
CRUD operations for TrainingPlan model.

Functions:
- create_training_plan: Create new training plan
- get_training_plan_by_id: Get training plan by ID
- get_training_plans_by_player: Get all training plans for a player
- get_training_plans_by_coach: Get all training plans created by a coach
- update_training_plan_status: Update training plan status
"""

from typing import Optional, List
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models.training_plan import TrainingPlan


def create_training_plan(
    db: Session,
    player_id: str,
    plan_title: str,
    created_by: Optional[str] = None,
    plan_description: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: str = "pending"
) -> TrainingPlan:
    """
    Create a new training plan.

    Args:
        db: Database session
        player_id: UUID of the player
        plan_title: Title of the training plan
        created_by: Optional UUID of the coach who created it
        plan_description: Optional description
        start_date: Optional start date
        end_date: Optional end date
        status: Status ('pending', 'in_progress', 'completed')

    Returns:
        Created TrainingPlan instance

    Example:
        >>> plan = create_training_plan(
        ...     db,
        ...     player_id="550e8400-...",
        ...     plan_title="Pre-season Conditioning",
        ...     created_by="660e8400-...",
        ...     plan_description="Focus on stamina and core strength",
        ...     status="pending"
        ... )
    """
    now = datetime.now(timezone.utc)

    training_plan = TrainingPlan(
        player_id=player_id,
        created_by=created_by,
        plan_title=plan_title,
        plan_description=plan_description,
        status=status,
        start_date=start_date,
        end_date=end_date,
        created_at=now,
        updated_at=now
    )

    db.add(training_plan)
    db.flush()
    db.refresh(training_plan)

    return training_plan


def get_training_plan_by_id(
    db: Session,
    plan_id: str
) -> Optional[TrainingPlan]:
    """
    Retrieve a training plan by ID.

    Args:
        db: Database session
        plan_id: TrainingPlan UUID

    Returns:
        TrainingPlan instance if found, None otherwise

    Example:
        >>> plan = get_training_plan_by_id(db, "550e8400-...")
        >>> if plan:
        ...     print(f"{plan.plan_title}: {plan.status}")
    """
    return db.query(TrainingPlan).filter(TrainingPlan.plan_id == plan_id).first()


def get_training_plans_by_player(
    db: Session,
    player_id: str,
    status: Optional[str] = None,
    limit: Optional[int] = None
) -> List[TrainingPlan]:
    """
    Get all training plans for a specific player.

    Args:
        db: Database session
        player_id: Player UUID
        status: Optional filter by status
        limit: Optional limit on number of results

    Returns:
        List of TrainingPlan instances ordered by created_at desc

    Example:
        >>> plans = get_training_plans_by_player(
        ...     db,
        ...     player_id="550e8400-...",
        ...     status="in_progress"
        ... )
        >>> for plan in plans:
        ...     print(f"{plan.plan_title}: {len(plan.exercises)} exercises")
    """
    query = db.query(TrainingPlan).filter(TrainingPlan.player_id == player_id)

    if status:
        query = query.filter(TrainingPlan.status == status)

    query = query.order_by(TrainingPlan.created_at.desc())

    if limit:
        query = query.limit(limit)

    return query.all()


def get_training_plans_by_coach(
    db: Session,
    coach_id: str,
    status: Optional[str] = None,
    limit: Optional[int] = None
) -> List[TrainingPlan]:
    """
    Get all training plans created by a specific coach.

    Args:
        db: Database session
        coach_id: Coach UUID
        status: Optional filter by status
        limit: Optional limit on number of results

    Returns:
        List of TrainingPlan instances ordered by created_at desc

    Example:
        >>> plans = get_training_plans_by_coach(db, "660e8400-...")
        >>> for plan in plans:
        ...     print(f"{plan.player.player_name}: {plan.plan_title}")
    """
    query = db.query(TrainingPlan).filter(TrainingPlan.created_by == coach_id)

    if status:
        query = query.filter(TrainingPlan.status == status)

    query = query.order_by(TrainingPlan.created_at.desc())

    if limit:
        query = query.limit(limit)

    return query.all()


def update_training_plan_status(
    db: Session,
    plan_id: str,
    status: str
) -> TrainingPlan:
    """
    Update training plan status.

    Args:
        db: Database session
        plan_id: TrainingPlan UUID
        status: New status ('pending', 'in_progress', 'completed')

    Returns:
        Updated TrainingPlan instance

    Raises:
        ValueError: If plan not found

    Example:
        >>> plan = update_training_plan_status(
        ...     db,
        ...     plan_id="550e8400-...",
        ...     status="completed"
        ... )
    """
    plan = get_training_plan_by_id(db, plan_id)

    if not plan:
        raise ValueError(f"Training plan not found: {plan_id}")

    plan.status = status
    plan.updated_at = datetime.now(timezone.utc)

    db.flush()
    db.refresh(plan)

    return plan
