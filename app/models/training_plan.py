"""
TrainingPlan Model

Stores training plans assigned to players.

Key Features:
- Assigned by coaches to individual players
- Status tracking (pending, in_progress, completed)
- Contains multiple exercises
"""

from sqlalchemy import Column, String, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, GUID, generate_uuid


class TrainingPlan(Base, TimestampMixin):
    """
    Training Plan Model

    Represents a training plan created by a coach for a player.

    Attributes:
        plan_id: Unique identifier
        player_id: Foreign key to player (CASCADE on delete)
        created_by: Foreign key to coach (SET NULL on delete)
        plan_name: Name of the training plan
        duration: Duration (e.g., "2 weeks")
        status: Current status ('pending', 'in_progress', 'completed')
        coach_notes: Instructions from coach
        created_at: Timestamp when plan was created
        updated_at: Timestamp when plan was last updated

    Relationships:
        - player: Many-to-one with Player model
        - coach: Many-to-one with Coach model
        - exercises: One-to-many with TrainingExercise model
    """

    __tablename__ = "training_plans"

    # Primary key
    plan_id = Column(
        GUID,
        primary_key=True,
        default=generate_uuid,
        comment="Unique plan ID"
    )

    # Foreign keys
    player_id = Column(
        GUID,
        ForeignKey("players.player_id", ondelete="CASCADE"),
        nullable=False,
        comment="Assigned player (CASCADE on deletion)"
    )

    created_by = Column(
        GUID,
        ForeignKey("coaches.coach_id", ondelete="SET NULL"),
        nullable=True,
        comment="Coach who created plan (SET NULL on deletion)"
    )

    # Plan information
    plan_name = Column(
        String(255),
        nullable=False,
        comment="Plan name"
    )

    duration = Column(
        String(50),
        nullable=True,
        comment="Duration (e.g., '2 weeks')"
    )

    status = Column(
        String(20),
        nullable=False,
        server_default="pending",
        comment="Status: 'pending', 'in_progress', 'completed'"
    )

    coach_notes = Column(
        Text,
        nullable=True,
        comment="Instructions from coach"
    )

    # Timestamps inherited from TimestampMixin
    # created_at, updated_at

    # Relationships
    player = relationship("Player", back_populates="training_plans")
    coach = relationship("Coach")
    exercises = relationship("TrainingExercise", back_populates="plan", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_training_plans_player_id", "player_id"),
        Index("idx_training_plans_status", "status"),
    )

    def __repr__(self):
        return f"<TrainingPlan(plan_id={self.plan_id}, player_id={self.player_id}, status='{self.status}')>"
