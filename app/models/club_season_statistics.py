"""
Club season statistics model for aggregated season-level club stats.
"""
from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.models.base import Base


class ClubSeasonStatistics(Base):
    """
    Aggregated season statistics for clubs.
    One record per club (UNIQUE constraint on club_id).
    Recalculated after each new match.
    Aggregated from match_statistics table.
    Used for coach dashboard display.
    """
    __tablename__ = "club_season_statistics"

    club_stats_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    club_id = Column(UUID(as_uuid=True), ForeignKey("clubs.club_id", ondelete="CASCADE"), unique=True, nullable=False)

    # Match Results
    matches_played = Column(Integer, nullable=False, default=0)
    wins = Column(Integer, nullable=False, default=0)
    draws = Column(Integer, nullable=False, default=0)
    losses = Column(Integer, nullable=False, default=0)

    # Goals
    goals_scored = Column(Integer, nullable=False, default=0)
    goals_conceded = Column(Integer, nullable=False, default=0)
    total_clean_sheets = Column(Integer, nullable=False, default=0)
    avg_goals_per_match = Column(Numeric(5, 2), nullable=True)
    avg_goals_conceded_per_match = Column(Numeric(5, 2), nullable=True)

    # Possession and Expected Goals
    avg_possession_percentage = Column(Numeric(5, 2), nullable=True)
    avg_xg_per_match = Column(Numeric(5, 2), nullable=True)

    # Shooting Statistics
    avg_total_shots = Column(Numeric(5, 2), nullable=True)
    avg_shots_on_target = Column(Numeric(5, 2), nullable=True)

    # Passing Statistics
    avg_total_passes = Column(Numeric(5, 2), nullable=True)
    pass_completion_rate = Column(Numeric(5, 2), nullable=True)  # Overall pass accuracy
    avg_final_third_passes = Column(Numeric(5, 2), nullable=True)
    avg_crosses = Column(Numeric(5, 2), nullable=True)

    # Dribbling Statistics
    avg_dribbles = Column(Numeric(5, 2), nullable=True)
    avg_successful_dribbles = Column(Numeric(5, 2), nullable=True)

    # Defensive Statistics
    avg_tackles = Column(Numeric(5, 2), nullable=True)
    tackle_success_rate = Column(Numeric(5, 2), nullable=True)  # Overall tackle success
    avg_interceptions = Column(Numeric(5, 2), nullable=True)
    interception_success_rate = Column(Numeric(5, 2), nullable=True)  # Overall interception success
    avg_ball_recoveries = Column(Numeric(5, 2), nullable=True)
    avg_saves_per_match = Column(Numeric(5, 2), nullable=True)  # Goalkeeper saves

    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    club = relationship("Club", back_populates="club_season_statistics", uselist=False)

    def __repr__(self):
        return f"<ClubSeasonStatistics(club_stats_id={self.club_stats_id}, club_id={self.club_id}, matches_played={self.matches_played})>"
