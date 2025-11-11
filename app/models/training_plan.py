"""
Training plan model for training plans assigned to players.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.models.base import Base


class TrainingPlan(Base):
    """
    Stores training plans assigned to players.
    Status automatically updated based on exercise completion:
    - 'pending': No exercises completed
    - 'in_progress': At least one exercise completed
    - 'completed': All exercises completed
    Training plans are NOT reused (no assignments table).
    """
    __tablename__ = "training_plans"

    plan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.player_id", ondelete="CASCADE"), nullable=False)
    plan_name = Column(String(255), nullable=False)
    duration = Column(String(50), nullable=True)  # e.g., "2 weeks"
    status = Column(String(20), nullable=False, default='pending')  # 'pending', 'in_progress', 'completed'
    coach_notes = Column(String, nullable=True)  # Instructions from coach
    created_by = Column(UUID(as_uuid=True), ForeignKey("coaches.coach_id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    player = relationship("Player", back_populates="training_plans")
    coach = relationship("Coach", back_populates="training_plans")
    exercises = relationship("TrainingExercise", back_populates="training_plan", cascade="all, delete-orphan", order_by="TrainingExercise.exercise_order")

    def __repr__(self):
        return f"<TrainingPlan(plan_id={self.plan_id}, plan_name='{self.plan_name}', status='{self.status}')>"
