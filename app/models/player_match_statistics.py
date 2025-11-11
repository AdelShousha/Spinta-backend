"""
PlayerMatchStatistics Model

Stores individual player statistics per match.

Key Features:
- One record per player per match
- Calculated from events table using statsbomb_player_id
- Aggregated into player_season_statistics
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Index, func, Numeric
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, generate_uuid


class PlayerMatchStatistics(Base):
    """
    Player Match Statistics Model

    Individual player performance statistics for a specific match.

    Attributes:
        player_match_stats_id: Unique identifier
        player_id: Foreign key to player (CASCADE on delete)
        match_id: Foreign key to match (CASCADE on delete)
        goals: Goals scored (default 0)
        assists: Assists (default 0)
        expected_goals: Player xG
        shots: Total shots
        shots_on_target: Shots on target
        total_dribbles: Dribbles attempted
        successful_dribbles: Successful dribbles
        total_passes: Total passes
        completed_passes: Completed passes
        short_passes: Short passes
        long_passes: Long passes
        final_third_passes: Passes in final third
        crosses: Crosses
        tackles: Tackles
        tackle_success_rate: Tackle success %
        interceptions: Interceptions
        interception_success_rate: Interception success %
        created_at: Timestamp when record was created

    Relationships:
        - player: Many-to-one with Player model
        - match: Many-to-one with Match model
    """

    __tablename__ = "player_match_statistics"

    # Primary key
    player_match_stats_id = Column(
        GUID,
        primary_key=True,
        default=generate_uuid,
        comment="Unique record ID"
    )

    # Foreign keys
    player_id = Column(
        GUID,
        ForeignKey("players.player_id", ondelete="CASCADE"),
        nullable=False,
        comment="Player reference (CASCADE on deletion)"
    )

    match_id = Column(
        GUID,
        ForeignKey("matches.match_id", ondelete="CASCADE"),
        nullable=False,
        comment="Match reference (CASCADE on deletion)"
    )

    # Statistics
    goals = Column(Integer, nullable=False, server_default="0", comment="Goals scored")
    assists = Column(Integer, nullable=False, server_default="0", comment="Assists")
    expected_goals = Column(Numeric(8, 6), nullable=True, comment="Player xG")
    shots = Column(Integer, nullable=True, comment="Total shots")
    shots_on_target = Column(Integer, nullable=True, comment="Shots on target")
    total_dribbles = Column(Integer, nullable=True, comment="Dribbles attempted")
    successful_dribbles = Column(Integer, nullable=True, comment="Successful dribbles")
    total_passes = Column(Integer, nullable=True, comment="Total passes")
    completed_passes = Column(Integer, nullable=True, comment="Completed passes")
    short_passes = Column(Integer, nullable=True, comment="Short passes")
    long_passes = Column(Integer, nullable=True, comment="Long passes")
    final_third_passes = Column(Integer, nullable=True, comment="Passes in final third")
    crosses = Column(Integer, nullable=True, comment="Crosses")
    tackles = Column(Integer, nullable=True, comment="Tackles")
    tackle_success_rate = Column(Numeric(5, 2), nullable=True, comment="Tackle success %")
    interceptions = Column(Integer, nullable=True, comment="Interceptions")
    interception_success_rate = Column(Numeric(5, 2), nullable=True, comment="Interception success %")

    # Timestamp (created_at only, no updated_at)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when record was created"
    )

    # Relationships
    player = relationship("Player")
    match = relationship("Match", back_populates="player_match_statistics")

    # Indexes
    __table_args__ = (
        Index("idx_player_match_statistics_player_id", "player_id"),
        Index("idx_player_match_statistics_match_id", "match_id"),
    )

    def __repr__(self):
        return f"<PlayerMatchStatistics(player_id={self.player_id}, match_id={self.match_id}, goals={self.goals})>"
