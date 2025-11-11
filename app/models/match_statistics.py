"""
Match statistics model for aggregated match-level stats.
"""
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.models.base import Base, GUID, generate_uuid


class MatchStatistics(Base):
    """
    Stores aggregated statistics per match (for both teams).
    Two records per match: one for 'our_team', one for 'opponent_team'.
    Calculated from events table after match processing.
    """
    __tablename__ = "match_statistics"

    statistics_id = Column(GUID, primary_key=True, default=generate_uuid)
    match_id = Column(GUID, ForeignKey("matches.match_id", ondelete="CASCADE"), nullable=False)
    team_type = Column(String(20), nullable=False)  # 'our_team' or 'opponent_team'

    # Possession and Expected Goals
    possession_percentage = Column(Numeric(5, 2), nullable=True)
    expected_goals = Column(Numeric(8, 6), nullable=True)  # StatsBomb xG uses up to 8 decimal places

    # Shooting Statistics
    total_shots = Column(Integer, nullable=True)
    shots_on_target = Column(Integer, nullable=True)
    shots_off_target = Column(Integer, nullable=True)
    goalkeeper_saves = Column(Integer, nullable=True)

    # Passing Statistics
    total_passes = Column(Integer, nullable=True)
    passes_completed = Column(Integer, nullable=True)
    pass_completion_rate = Column(Numeric(5, 2), nullable=True)
    passes_in_final_third = Column(Integer, nullable=True)
    long_passes = Column(Integer, nullable=True)
    crosses = Column(Integer, nullable=True)

    # Dribbling Statistics
    total_dribbles = Column(Integer, nullable=True)
    successful_dribbles = Column(Integer, nullable=True)

    # Defensive Statistics
    total_tackles = Column(Integer, nullable=True)
    tackle_success_percentage = Column(Numeric(5, 2), nullable=True)
    interceptions = Column(Integer, nullable=True)
    ball_recoveries = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    match = relationship("Match", back_populates="match_statistics")

    __table_args__ = (
        UniqueConstraint('match_id', 'team_type', name='uq_match_statistics_match_team'),
    )

    def __repr__(self):
        return f"<MatchStatistics(statistics_id={self.statistics_id}, match_id={self.match_id}, team_type='{self.team_type}')>"
