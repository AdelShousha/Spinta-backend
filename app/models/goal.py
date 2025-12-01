"""
Goal Model

Stores goal events from matches extracted from StatsBomb event data.

Key Features:
- Extracted from StatsBomb shot events with successful outcomes
- Used for goals timeline display in match details
- is_our_goal indicates whether it was scored by our team or opponent
"""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Index, func
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, generate_uuid
from datetime import datetime, timezone


class Goal(Base):
    """
    Goal Model

    Represents a goal scored during a match.

    Attributes:
        goal_id: Unique identifier for the goal
        match_id: Foreign key to match (CASCADE on delete)
        scorer_name: Player who scored
        minute: Match minute when goal was scored
        second: Second within minute (nullable)
        is_our_goal: True if scored by our team, False if opponent
        created_at: Timestamp when record was created

    Relationships:
        - match: Many-to-one with Match model
    """

    __tablename__ = "goals"

    # Primary key
    goal_id = Column(
        GUID,
        primary_key=True,
        default=generate_uuid,
        comment="Unique goal identifier"
    )

    # Foreign key
    match_id = Column(
        GUID,
        ForeignKey("matches.match_id", ondelete="CASCADE"),
        nullable=False,
        comment="Match reference (CASCADE on deletion)"
    )

    # Goal information
    scorer_name = Column(
        String(255),
        nullable=False,
        comment="Player who scored"
    )

    minute = Column(
        Integer,
        nullable=False,
        comment="Match minute"
    )

    second = Column(
        Integer,
        nullable=True,
        comment="Second within minute"
    )

    is_our_goal = Column(
        Boolean,
        nullable=False,
        comment="True if scored by our team, False if opponent"
    )

    # Timestamp (created_at only, no updated_at)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Timestamp when record was created"
    )

    # Relationships
    match = relationship("Match")

    # Indexes
    __table_args__ = (
        Index("idx_goals_match_id", "match_id"),
    )

    def __repr__(self):
        return f"<Goal(goal_id={self.goal_id}, scorer='{self.scorer_name}', minute={self.minute})>"
