"""
Goal model for storing goal events from matches.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.models.base import Base, GUID, generate_uuid


class Goal(Base):
    """
    Stores goal events extracted from StatsBomb match data.
    Used for goals timeline display in match details.
    """
    __tablename__ = "goals"

    goal_id = Column(GUID, primary_key=True, default=generate_uuid)
    match_id = Column(GUID, ForeignKey("matches.match_id", ondelete="CASCADE"), nullable=False)
    team_name = Column(String(255), nullable=False)  # Can be our club or opponent
    scorer_name = Column(String(255), nullable=False)
    assist_name = Column(String(255), nullable=True)
    minute = Column(Integer, nullable=False)
    second = Column(Integer, nullable=True)
    period = Column(Integer, nullable=False)
    goal_type = Column(String(50), nullable=True)  # "Open Play", "Penalty", "Free Kick", etc.
    body_part = Column(String(50), nullable=True)  # "Right Foot", "Left Foot", "Head", etc.
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    match = relationship("Match", back_populates="goals")

    def __repr__(self):
        return f"<Goal(goal_id={self.goal_id}, scorer_name='{self.scorer_name}', minute={self.minute}, team_name='{self.team_name}')>"
