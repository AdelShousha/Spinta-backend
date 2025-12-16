"""
TrainingExercise Model

Stores individual exercises within training plans.

Key Features:
- Part of a training plan
- Completion tracking by player
- Numeric parameters (sets, reps, duration as integers)
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Index, Text, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, GUID, generate_uuid


class TrainingExercise(Base, TimestampMixin):
    """
    Training Exercise Model

    Represents a single exercise within a training plan.

    Attributes:
        exercise_id: Unique identifier
        plan_id: Foreign key to training plan (CASCADE on delete)
        exercise_name: Name of the exercise
        description: Exercise description/instructions
        sets: Number of sets (integer)
        reps: Number of reps (integer)
        duration_minutes: Duration in minutes (integer)
        exercise_order: Display order within the plan
        completed: Has player completed this exercise?
        completed_at: When player marked it complete
        created_at: Timestamp when exercise was created
        updated_at: Timestamp when exercise was last updated

    Relationships:
        - plan: Many-to-one with TrainingPlan model
    """

    __tablename__ = "training_exercises"

    # Primary key
    exercise_id = Column(
        GUID,
        primary_key=True,
        default=generate_uuid,
        comment="Unique exercise ID"
    )

    # Foreign key
    plan_id = Column(
        GUID,
        ForeignKey("training_plans.plan_id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent plan (CASCADE on deletion)"
    )

    # Exercise information
    exercise_name = Column(
        String(255),
        nullable=False,
        comment="Exercise name"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Exercise description/instructions"
    )

    sets = Column(
        Integer,
        nullable=True,
        comment="Number of sets"
    )

    reps = Column(
        Integer,
        nullable=True,
        comment="Number of reps"
    )

    duration_minutes = Column(
        Integer,
        nullable=True,
        comment="Duration in minutes"
    )

    exercise_order = Column(
        Integer,
        nullable=False,
        comment="Display order within the plan"
    )

    # Completion tracking
    completed = Column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Has player completed this exercise?"
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When player marked it complete"
    )

    # Timestamps inherited from TimestampMixin
    # created_at, updated_at

    # Relationships
    plan = relationship("TrainingPlan", back_populates="exercises")

    # Indexes
    __table_args__ = (
        Index("idx_training_exercises_plan_id", "plan_id"),
    )

    def __repr__(self):
        return f"<TrainingExercise(exercise_id={self.exercise_id}, name='{self.exercise_name}', completed={self.completed})>"
