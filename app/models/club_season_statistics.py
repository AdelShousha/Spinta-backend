"""
ClubSeasonStatistics Model

Aggregated season statistics for clubs.

Key Features:
- One record per club (UNIQUE constraint on club_id)
- Recalculated after each new match
- Aggregated from match_statistics table
- Used for coach dashboard display
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Index, func, Numeric
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, generate_uuid


class ClubSeasonStatistics(Base):
    """
    Club Season Statistics Model

    Aggregated season-level statistics for a club.

    Attributes:
        club_stats_id: Unique identifier
        club_id: Foreign key to club (UNIQUE, CASCADE on delete)
        matches_played: Total matches played
        wins: Wins
        draws: Draws
        losses: Losses
        goals_scored: Total goals scored
        goals_conceded: Total goals conceded
        total_clean_sheets: Clean sheets
        avg_goals_per_match: Avg goals per match
        avg_possession_percentage: Avg possession %
        avg_total_shots: Avg shots per match
        avg_shots_on_target: Avg shots on target
        avg_xg_per_match: Avg xG per match
        avg_goals_conceded_per_match: Avg goals conceded
        avg_total_passes: Avg passes per match
        pass_completion_rate: Overall pass accuracy %
        avg_final_third_passes: Avg final third passes
        avg_crosses: Avg crosses per match
        avg_dribbles: Avg dribbles per match
        avg_successful_dribbles: Avg successful dribbles
        avg_tackles: Avg tackles per match
        tackle_success_rate: Overall tackle success %
        avg_interceptions: Avg interceptions
        interception_success_rate: Overall interception success %
        avg_ball_recoveries: Avg ball recoveries
        avg_saves_per_match: Avg goalkeeper saves
        updated_at: Last calculation time

    Relationships:
        - club: One-to-one with Club model
    """

    __tablename__ = "club_season_statistics"

    # Primary key
    club_stats_id = Column(
        GUID,
        primary_key=True,
        default=generate_uuid,
        comment="Unique record ID"
    )

    # Foreign key (UNIQUE for one-to-one relationship)
    club_id = Column(
        GUID,
        ForeignKey("clubs.club_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="Club reference (CASCADE on deletion, UNIQUE)"
    )

    # Match results
    matches_played = Column(Integer, nullable=False, server_default="0", comment="Total matches played")
    wins = Column(Integer, nullable=False, server_default="0", comment="Wins")
    draws = Column(Integer, nullable=False, server_default="0", comment="Draws")
    losses = Column(Integer, nullable=False, server_default="0", comment="Losses")
    goals_scored = Column(Integer, nullable=False, server_default="0", comment="Total goals scored")
    goals_conceded = Column(Integer, nullable=False, server_default="0", comment="Total goals conceded")
    total_clean_sheets = Column(Integer, nullable=False, server_default="0", comment="Clean sheets")

    # Averages and rates
    avg_goals_per_match = Column(Numeric(5, 2), nullable=True, comment="Avg goals per match")
    avg_possession_percentage = Column(Numeric(5, 2), nullable=True, comment="Avg possession %")
    avg_total_shots = Column(Numeric(5, 2), nullable=True, comment="Avg shots per match")
    avg_shots_on_target = Column(Numeric(5, 2), nullable=True, comment="Avg shots on target")
    avg_xg_per_match = Column(Numeric(5, 2), nullable=True, comment="Avg xG per match")
    avg_goals_conceded_per_match = Column(Numeric(5, 2), nullable=True, comment="Avg goals conceded")
    avg_total_passes = Column(Numeric(5, 2), nullable=True, comment="Avg passes per match")
    pass_completion_rate = Column(Numeric(5, 2), nullable=True, comment="Overall pass accuracy %")
    avg_final_third_passes = Column(Numeric(5, 2), nullable=True, comment="Avg final third passes")
    avg_crosses = Column(Numeric(5, 2), nullable=True, comment="Avg crosses per match")
    avg_dribbles = Column(Numeric(5, 2), nullable=True, comment="Avg dribbles per match")
    avg_successful_dribbles = Column(Numeric(5, 2), nullable=True, comment="Avg successful dribbles")
    avg_tackles = Column(Numeric(5, 2), nullable=True, comment="Avg tackles per match")
    tackle_success_rate = Column(Numeric(5, 2), nullable=True, comment="Overall tackle success %")
    avg_interceptions = Column(Numeric(5, 2), nullable=True, comment="Avg interceptions")
    interception_success_rate = Column(Numeric(5, 2), nullable=True, comment="Overall interception success %")
    avg_ball_recoveries = Column(Numeric(5, 2), nullable=True, comment="Avg ball recoveries")
    avg_saves_per_match = Column(Numeric(5, 2), nullable=True, comment="Avg goalkeeper saves")

    # Timestamp (updated_at only)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last calculation time"
    )

    # Relationships
    club = relationship("Club", back_populates="season_statistics", uselist=False)

    # Indexes
    __table_args__ = (
        Index("idx_club_season_statistics_club_id", "club_id", unique=True),
    )

    def __repr__(self):
        return f"<ClubSeasonStatistics(club_id={self.club_id}, matches={self.matches_played}, wins={self.wins})>"
