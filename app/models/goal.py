"""
Goal Model

Stores goal events from matches extracted from StatsBomb event data.

Key Features:
- Extracted from StatsBomb shot events with successful outcomes
- Used for goals timeline display in match details
- team_name can be our club or opponent
- assist_name is nullable (not all goals have assists)
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Index, func
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, generate_uuid


class Goal(Base):
    """
    Goal Model

    Represents a goal scored during a match.

    Attributes:
        goal_id: Unique identifier for the goal
        match_id: Foreign key to match (CASCADE on delete)
        team_name: Team that scored the goal
        scorer_name: Player who scored
        assist_name: Player who assisted (nullable)
        minute: Match minute when goal was scored
        second: Second within minute (nullable)
        period: Match period (1, 2, etc.)
        goal_type: Type of goal (Open Play, Penalty, etc.)
        body_part: Body part used (Right Foot, Header, etc.)
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
    team_name = Column(
        String(255),
        nullable=False,
        comment="Team that scored"
    )

    scorer_name = Column(
        String(255),
        nullable=False,
        comment="Player who scored"
    )

    assist_name = Column(
        String(255),
        nullable=True,
        comment="Player who assisted (nullable)"
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

    period = Column(
        Integer,
        nullable=False,
        comment="Match period (1, 2, etc.)"
    )

    goal_type = Column(
        String(50),
        nullable=True,
        comment="Type of goal (Open Play, Penalty, etc.)"
    )

    body_part = Column(
        String(50),
        nullable=True,
        comment="Body part used (Right Foot, Header, etc.)"
    )

    # Timestamp (created_at only, no updated_at)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
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
