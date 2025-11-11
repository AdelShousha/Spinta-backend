"""
Player season statistics model for aggregated season-level player stats.
"""
from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.models.base import Base


class PlayerSeasonStatistics(Base):
    """
    Aggregated season statistics for players.
    One record per player (UNIQUE constraint on player_id).
    Recalculated after each new match.
    Aggregated from player_match_statistics table.
    Includes calculated attributes (0-100 ratings).
    Used for player dashboard and profile screens.
    Exists for all players (both linked and unlinked).
    """
    __tablename__ = "player_season_statistics"

    player_stats_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.player_id", ondelete="CASCADE"), unique=True, nullable=False)

    # Match Count
    matches_played = Column(Integer, nullable=False, default=0)

    # Goal Statistics
    goals = Column(Integer, nullable=False, default=0)
    assists = Column(Integer, nullable=False, default=0)
    expected_goals = Column(Numeric(8, 6), nullable=True)  # Total xG, StatsBomb uses up to 8 decimal places

    # Shooting Statistics
    shots_per_game = Column(Numeric(5, 2), nullable=True)
    shots_on_target_per_game = Column(Numeric(5, 2), nullable=True)

    # Passing Statistics
    total_passes = Column(Integer, nullable=True)
    passes_completed = Column(Integer, nullable=True)

    # Dribbling Statistics
    total_dribbles = Column(Integer, nullable=True)
    successful_dribbles = Column(Integer, nullable=True)

    # Defensive Statistics
    tackles = Column(Integer, nullable=True)
    tackle_success_rate = Column(Numeric(5, 2), nullable=True)
    interceptions = Column(Integer, nullable=True)
    interception_success_rate = Column(Numeric(5, 2), nullable=True)

    # Player Attributes (0-100 ratings calculated from stats)
    attacking_rating = Column(Integer, nullable=True)  # Based on goals, assists, xG, shots
    technique_rating = Column(Integer, nullable=True)  # Based on dribbles, pass completion
    tactical_rating = Column(Integer, nullable=True)  # Based on positioning, decision-making
    defending_rating = Column(Integer, nullable=True)  # Based on tackles, interceptions
    creativity_rating = Column(Integer, nullable=True)  # Based on assists, key passes, final third activity

    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    player = relationship("Player", back_populates="player_season_statistics", uselist=False)

    def __repr__(self):
        return f"<PlayerSeasonStatistics(player_stats_id={self.player_stats_id}, player_id={self.player_id}, goals={self.goals}, assists={self.assists})>"
