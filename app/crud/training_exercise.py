"""
CRUD operations for TrainingExercise model.

Functions:
- create_training_exercise: Create new training exercise
- get_training_exercises_by_plan: Get all exercises for a training plan
- update_exercise_completion: Mark exercise as completed/uncompleted
"""

from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.training_exercise import TrainingExercise


def create_training_exercise(
    db: Session,
    plan_id: str,
    exercise_title: str,
    exercise_order: int,
    exercise_description: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    repetitions: Optional[int] = None,
    sets: Optional[int] = None
) -> TrainingExercise:
    """
    Create a new training exercise.

    Args:
        db: Database session
        plan_id: UUID of the training plan
        exercise_title: Title of the exercise
        exercise_order: Display order (1, 2, 3, ...)
        exercise_description: Optional description
        duration_minutes: Optional duration in minutes
        repetitions: Optional number of repetitions
        sets: Optional number of sets

    Returns:
        Created TrainingExercise instance

    Example:
        >>> exercise = create_training_exercise(
        ...     db,
        ...     plan_id="550e8400-...",
        ...     exercise_title="Sprint intervals",
        ...     exercise_order=1,
        ...     exercise_description="10x50m sprints with 30s rest",
        ...     duration_minutes=20,
        ...     repetitions=10
        ... )
    """
    training_exercise = TrainingExercise(
        plan_id=plan_id,
        exercise_title=exercise_title,
        exercise_description=exercise_description,
        exercise_order=exercise_order,
        duration_minutes=duration_minutes,
        repetitions=repetitions,
        sets=sets,
        completed=False,
        created_at=datetime.now(timezone.utc)
    )

    db.add(training_exercise)
    db.flush()
    db.refresh(training_exercise)

    return training_exercise


def get_training_exercises_by_plan(
    db: Session,
    plan_id: str,
    completed: Optional[bool] = None
) -> List[TrainingExercise]:
    """
    Get all exercises for a specific training plan.

    Args:
        db: Database session
        plan_id: TrainingPlan UUID
        completed: Optional filter by completion status

    Returns:
        List of TrainingExercise instances ordered by exercise_order

    Example:
        >>> exercises = get_training_exercises_by_plan(db, "550e8400-...")
        >>> for ex in exercises:
        ...     status = "✓" if ex.completed else "○"
        ...     print(f"{status} {ex.exercise_order}. {ex.exercise_title}")
    """
    query = db.query(TrainingExercise).filter(TrainingExercise.plan_id == plan_id)

    if completed is not None:
        query = query.filter(TrainingExercise.completed == completed)

    query = query.order_by(TrainingExercise.exercise_order)

    return query.all()


def update_exercise_completion(
    db: Session,
    exercise_id: str,
    completed: bool
) -> TrainingExercise:
    """
    Mark exercise as completed or uncompleted.

    Args:
        db: Database session
        exercise_id: TrainingExercise UUID
        completed: True to mark as completed, False to mark as uncompleted

    Returns:
        Updated TrainingExercise instance

    Raises:
        ValueError: If exercise not found

    Example:
        >>> exercise = update_exercise_completion(
        ...     db,
        ...     exercise_id="550e8400-...",
        ...     completed=True
        ... )
        >>> print(f"Completed at: {exercise.completed_at}")
    """
    exercise = db.query(TrainingExercise).filter(
        TrainingExercise.exercise_id == exercise_id
    ).first()

    if not exercise:
        raise ValueError(f"Training exercise not found: {exercise_id}")

    exercise.completed = completed

    if completed:
        exercise.completed_at = datetime.now(timezone.utc)
    else:
        exercise.completed_at = None

    db.flush()
    db.refresh(exercise)

    # Check if all exercises in the plan are completed
    # and update the training plan status accordingly
    all_exercises = get_training_exercises_by_plan(db, exercise.plan_id)
    all_completed = all(ex.completed for ex in all_exercises)

    if all_completed and exercise.training_plan:
        exercise.training_plan.status = "completed"
        exercise.training_plan.updated_at = datetime.now(timezone.utc)
    elif exercise.completed and exercise.training_plan and exercise.training_plan.status == "pending":
        # If at least one exercise is completed and plan is still pending, mark as in_progress
        exercise.training_plan.status = "in_progress"
        exercise.training_plan.updated_at = datetime.now(timezone.utc)

    return exercise
