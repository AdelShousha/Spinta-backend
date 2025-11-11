"""
Player match statistics model for individual player stats per match.
"""
from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.models.base import Base


class PlayerMatchStatistics(Base):
    """
    Stores individual player statistics per match.
    One record per player per match.
    Calculated from events table using statsbomb_player_id.
    Aggregated into player_season_statistics.
    """
    __tablename__ = "player_match_statistics"

    player_match_stats_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.player_id", ondelete="CASCADE"), nullable=False)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.match_id", ondelete="CASCADE"), nullable=False)

    # Goal Statistics
    goals = Column(Integer, nullable=False, default=0)
    assists = Column(Integer, nullable=False, default=0)
    expected_goals = Column(Numeric(8, 6), nullable=True)  # StatsBomb xG uses up to 8 decimal places

    # Shooting Statistics
    shots = Column(Integer, nullable=True)
    shots_on_target = Column(Integer, nullable=True)

    # Dribbling Statistics
    total_dribbles = Column(Integer, nullable=True)
    successful_dribbles = Column(Integer, nullable=True)

    # Passing Statistics
    total_passes = Column(Integer, nullable=True)
    completed_passes = Column(Integer, nullable=True)
    short_passes = Column(Integer, nullable=True)
    long_passes = Column(Integer, nullable=True)
    final_third_passes = Column(Integer, nullable=True)
    crosses = Column(Integer, nullable=True)

    # Defensive Statistics
    tackles = Column(Integer, nullable=True)
    tackle_success_rate = Column(Numeric(5, 2), nullable=True)
    interceptions = Column(Integer, nullable=True)
    interception_success_rate = Column(Numeric(5, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    player = relationship("Player", back_populates="player_match_statistics")
    match = relationship("Match", back_populates="player_match_statistics")

    __table_args__ = (
        UniqueConstraint('player_id', 'match_id', name='uq_player_match_statistics_player_match'),
    )

    def __repr__(self):
        return f"<PlayerMatchStatistics(player_match_stats_id={self.player_match_stats_id}, player_id={self.player_id}, match_id={self.match_id})>"
