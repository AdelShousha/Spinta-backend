"""
PlayerSeasonStatistics Model

Aggregated season statistics for players.

Key Features:
- One record per player (UNIQUE constraint on player_id)
- Recalculated after each new match
- Aggregated from player_match_statistics table
- Attributes calculated from season stats using formulas
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Index, func, Numeric
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, generate_uuid


class PlayerSeasonStatistics(Base):
    """
    Player Season Statistics Model

    Aggregated season-level statistics for a player.

    Attributes:
        player_stats_id: Unique identifier
        player_id: Foreign key to player (UNIQUE, CASCADE on delete)
        matches_played: Matches played
        goals: Total goals
        assists: Total assists
        expected_goals: Total xG
        shots_per_game: Avg shots per game
        shots_on_target_per_game: Avg shots on target
        total_passes: Total passes
        passes_completed: Completed passes
        total_dribbles: Total dribbles
        successful_dribbles: Successful dribbles
        tackles: Total tackles
        tackle_success_rate: Tackle success %
        interceptions: Total interceptions
        interception_success_rate: Interception success %
        attacking_rating: Attacking attribute (0-100)
        technique_rating: Technique attribute (0-100)
        tactical_rating: Tactical attribute (0-100)
        defending_rating: Defending attribute (0-100)
        creativity_rating: Creativity attribute (0-100)
        updated_at: Last calculation time

    Relationships:
        - player: One-to-one with Player model
    """

    __tablename__ = "player_season_statistics"

    # Primary key
    player_stats_id = Column(
        GUID,
        primary_key=True,
        default=generate_uuid,
        comment="Unique record ID"
    )

    # Foreign key (UNIQUE for one-to-one relationship)
    player_id = Column(
        GUID,
        ForeignKey("players.player_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="Player reference (CASCADE on deletion, UNIQUE)"
    )

    # Basic statistics
    matches_played = Column(Integer, nullable=False, server_default="0", comment="Matches played")
    goals = Column(Integer, nullable=False, server_default="0", comment="Total goals")
    assists = Column(Integer, nullable=False, server_default="0", comment="Total assists")
    expected_goals = Column(Numeric(8, 6), nullable=True, comment="Total xG")
    shots_per_game = Column(Numeric(5, 2), nullable=True, comment="Avg shots per game")
    shots_on_target_per_game = Column(Numeric(5, 2), nullable=True, comment="Avg shots on target")

    # Passing and possession
    total_passes = Column(Integer, nullable=True, comment="Total passes")
    passes_completed = Column(Integer, nullable=True, comment="Completed passes")

    # Dribbling
    total_dribbles = Column(Integer, nullable=True, comment="Total dribbles")
    successful_dribbles = Column(Integer, nullable=True, comment="Successful dribbles")

    # Defensive statistics
    tackles = Column(Integer, nullable=True, comment="Total tackles")
    tackle_success_rate = Column(Numeric(5, 2), nullable=True, comment="Tackle success %")
    interceptions = Column(Integer, nullable=True, comment="Total interceptions")
    interception_success_rate = Column(Numeric(5, 2), nullable=True, comment="Interception success %")

    # Player attributes/ratings (0-100)
    attacking_rating = Column(Integer, nullable=True, comment="Attacking attribute (0-100)")
    technique_rating = Column(Integer, nullable=True, comment="Technique attribute (0-100)")
    tactical_rating = Column(Integer, nullable=True, comment="Tactical attribute (0-100)")
    defending_rating = Column(Integer, nullable=True, comment="Defending attribute (0-100)")
    creativity_rating = Column(Integer, nullable=True, comment="Creativity attribute (0-100)")

    # Timestamp (updated_at only)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last calculation time"
    )

    # Relationships
    player = relationship("Player", back_populates="season_statistics", uselist=False)

    # Indexes
    __table_args__ = (
        Index("idx_player_season_statistics_player_id", "player_id", unique=True),
    )

    def __repr__(self):
        return f"<PlayerSeasonStatistics(player_id={self.player_id}, goals={self.goals}, assists={self.assists})>"
