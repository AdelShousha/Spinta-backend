"""
Match Model

Stores match records between our club and opponent clubs.

Key Features:
- Links to both our club and opponent club
- Denormalized opponent_name for easier queries
- Scores are NULL until match is completed
- Created by coach uploading match video and StatsBomb data
"""

from sqlalchemy import Column, String, Date, Time, Boolean, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, GUID, generate_uuid


class Match(Base, TimestampMixin):
    """
    Match Model

    Represents a match between our club and an opponent club.

    Attributes:
        match_id: Unique identifier for the match
        club_id: Foreign key to our club (nullable, SET NULL on delete)
        opponent_club_id: Foreign key to opponent club (CASCADE on delete)
        opponent_name: Denormalized opponent name for easier queries
        match_date: Date when the match took place
        match_time: Kickoff time (nullable)
        is_home_match: True if home match, False if away
        home_score: Final home team score (nullable until match complete)
        away_score: Final away team score (nullable until match complete)
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated

    Relationships:
        - club: Many-to-one with Club model
        - opponent_club: Many-to-one with OpponentClub model
        - goals: One-to-many with Goal model (CASCADE delete)
        - events: One-to-many with Event model (CASCADE delete)
        - match_statistics: One-to-one with MatchStatistics model
    """

    __tablename__ = "matches"

    # Primary key
    match_id = Column(
        GUID,
        primary_key=True,
        default=generate_uuid,
        comment="Unique match identifier"
    )

    # Foreign keys
    club_id = Column(
        GUID,
        ForeignKey("clubs.club_id", ondelete="CASCADE"),
        nullable=False,
        comment="Our club (CASCADE on deletion)"
    )

    opponent_club_id = Column(
        GUID,
        ForeignKey("opponent_clubs.opponent_club_id", ondelete="CASCADE"),
        nullable=True,
        comment="Opponent club (CASCADE on deletion, nullable)"
    )

    # Match information
    opponent_name = Column(
        String(255),
        nullable=False,
        comment="Opponent name (denormalized for easier queries)"
    )

    match_date = Column(
        Date,
        nullable=False,
        comment="Match date"
    )

    match_time = Column(
        Time,
        nullable=True,
        comment="Match kickoff time"
    )

    is_home_match = Column(
        Boolean,
        nullable=False,
        comment="Is this a home match?"
    )

    home_score = Column(
        Integer,
        nullable=True,
        comment="Final home team score (NULL until match complete)"
    )

    away_score = Column(
        Integer,
        nullable=True,
        comment="Final away team score (NULL until match complete)"
    )

    # Timestamps inherited from TimestampMixin
    # created_at, updated_at

    # Relationships
    club = relationship("Club", back_populates="matches")
    opponent_club = relationship("OpponentClub", back_populates="matches")
    goals = relationship("Goal", back_populates="match", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="match", cascade="all, delete-orphan")
    match_statistics = relationship("MatchStatistics", back_populates="match", cascade="all, delete-orphan")
    player_match_statistics = relationship("PlayerMatchStatistics", back_populates="match", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_matches_club_id", "club_id"),
        Index("idx_matches_match_date", "match_date"),
    )

    def __repr__(self):
        return f"<Match(match_id={self.match_id}, opponent_name='{self.opponent_name}', date={self.match_date})>"
