"""
MatchStatistics Model

Stores aggregated statistics per match (for both teams).

Key Features:
- 2 records per match (our_team, opponent_team)
- Calculated from events table after match processing
- Used for match detail screen statistics comparison
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Index, CheckConstraint, func, Numeric
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, generate_uuid
from datetime import datetime, timezone


class MatchStatistics(Base):
    """
    Match Statistics Model

    Aggregated statistics for a match (one record each for our team and opponent).

    Attributes:
        statistics_id: Unique identifier
        match_id: Foreign key to match (CASCADE on delete)
        team_type: 'our_team' or 'opponent_team'
        possession_percentage: Ball possession %
        expected_goals: xG (StatsBomb uses up to 8 decimal places)
        total_shots: Total shots
        shots_on_target: Shots on target
        shots_off_target: Shots off target
        goalkeeper_saves: Saves by goalkeeper
        total_passes: Total passes
        passes_completed: Completed passes
        pass_completion_rate: Pass accuracy %
        passes_in_final_third: Passes in final third
        long_passes: Long passes
        crosses: Crosses
        total_dribbles: Dribbles attempted
        successful_dribbles: Successful dribbles
        total_tackles: Tackles attempted
        tackle_success_percentage: Tackle success %
        interceptions: Interceptions
        ball_recoveries: Ball recoveries
        created_at: Timestamp when record was created

    Relationships:
        - match: Many-to-one with Match model
    """

    __tablename__ = "match_statistics"

    # Primary key
    statistics_id = Column(
        GUID,
        primary_key=True,
        default=generate_uuid,
        comment="Unique statistics record ID"
    )

    # Foreign key
    match_id = Column(
        GUID,
        ForeignKey("matches.match_id", ondelete="CASCADE"),
        nullable=False,
        comment="Match reference (CASCADE on deletion)"
    )

    # Team identifier
    team_type = Column(
        String(20),
        nullable=False,
        comment="'our_team' or 'opponent_team'"
    )

    # Match statistics
    possession_percentage = Column(Numeric(5, 2), nullable=True, comment="Ball possession %")
    expected_goals = Column(Numeric(8, 6), nullable=True, comment="xG (StatsBomb uses up to 8 decimal places)")
    total_shots = Column(Integer, nullable=True, comment="Total shots")
    shots_on_target = Column(Integer, nullable=True, comment="Shots on target")
    shots_off_target = Column(Integer, nullable=True, comment="Shots off target")
    goalkeeper_saves = Column(Integer, nullable=True, comment="Saves by goalkeeper")
    total_passes = Column(Integer, nullable=True, comment="Total passes")
    passes_completed = Column(Integer, nullable=True, comment="Completed passes")
    pass_completion_rate = Column(Numeric(5, 2), nullable=True, comment="Pass accuracy %")
    passes_in_final_third = Column(Integer, nullable=True, comment="Passes in final third")
    long_passes = Column(Integer, nullable=True, comment="Long passes")
    crosses = Column(Integer, nullable=True, comment="Crosses")
    total_dribbles = Column(Integer, nullable=True, comment="Dribbles attempted")
    successful_dribbles = Column(Integer, nullable=True, comment="Successful dribbles")
    total_tackles = Column(Integer, nullable=True, comment="Tackles attempted")
    tackle_success_percentage = Column(Numeric(5, 2), nullable=True, comment="Tackle success %")
    interceptions = Column(Integer, nullable=True, comment="Interceptions")
    ball_recoveries = Column(Integer, nullable=True, comment="Ball recoveries")

    # Timestamp (created_at only, no updated_at)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Timestamp when record was created"
    )

    # Relationships
    match = relationship("Match", back_populates="match_statistics")

    # Indexes and constraints
    __table_args__ = (
        Index("idx_match_statistics_match_id", "match_id"),
        CheckConstraint("team_type IN ('our_team', 'opponent_team')", name="ck_match_statistics_team_type"),
        CheckConstraint("match_id IS NOT NULL AND team_type IS NOT NULL", name="uq_match_statistics_match_team"),
    )

    def __repr__(self):
        return f"<MatchStatistics(statistics_id={self.statistics_id}, match_id={self.match_id}, team='{self.team_type}')>"
