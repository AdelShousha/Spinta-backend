"""
Training exercise model for exercises within training plans.
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.models.base import Base


class TrainingExercise(Base):
    """
    Stores individual exercises within training plans.
    Player toggles 'completed' flag from mobile app.
    When completed changes to TRUE:
    - completed_at set to NOW()
    - Parent plan status updated to 'in_progress' (if was 'pending')
    When all exercises completed:
    - Parent plan status updated to 'completed'
    Player can uncheck exercises (toggle back to FALSE).
    """
    __tablename__ = "training_exercises"

    exercise_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("training_plans.plan_id", ondelete="CASCADE"), nullable=False)
    exercise_name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    sets = Column(String(20), nullable=True)  # Stored as string for flexibility
    reps = Column(String(20), nullable=True)  # Stored as string for flexibility
    duration_minutes = Column(String(20), nullable=True)  # Stored as string for flexibility
    exercise_order = Column(Integer, nullable=False)  # Display order
    completed = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    training_plan = relationship("TrainingPlan", back_populates="exercises")

    def __repr__(self):
        return f"<TrainingExercise(exercise_id={self.exercise_id}, exercise_name='{self.exercise_name}', completed={self.completed})>"
