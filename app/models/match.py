"""
Match Model

Stores match records between our club and opponent clubs.

Key Features:
- Links to both our club and opponent club
- Denormalized opponent_name for easier queries
- Scores and result are NULL until match is completed
- Created by coach uploading match video and StatsBomb data
"""

from sqlalchemy import Column, String, Date, Integer, ForeignKey, DateTime, Index, func
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, generate_uuid
from datetime import datetime, timezone


class Match(Base):
    """
    Match Model

    Represents a match between our club and an opponent club.

    Attributes:
        match_id: Unique identifier for the match
        club_id: Foreign key to our club (CASCADE on delete)
        opponent_club_id: Foreign key to opponent club (CASCADE on delete)
        opponent_name: Denormalized opponent name for easier queries
        match_date: Date when the match took place
        our_score: Our club's final score (nullable until match complete)
        opponent_score: Opponent's final score (nullable until match complete)
        result: Match result from our perspective: W/D/L (nullable until match complete)
        created_at: Timestamp when record was created

    Relationships:
        - club: Many-to-one with Club model
        - opponent_club: Many-to-one with OpponentClub model
        - goals: One-to-many with Goal model (CASCADE delete)
        - events: One-to-many with Event model (CASCADE delete)
        - match_statistics: One-to-many with MatchStatistics model (CASCADE delete)
        - player_match_statistics: One-to-many with PlayerMatchStatistics model (CASCADE delete)
        - lineups: One-to-many with MatchLineup model (CASCADE delete)
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

    our_score = Column(
        Integer,
        nullable=True,
        comment="Our club's final score (NULL until match complete)"
    )

    opponent_score = Column(
        Integer,
        nullable=True,
        comment="Opponent's final score (NULL until match complete)"
    )

    result = Column(
        String(1),
        nullable=True,
        comment="Match result from our perspective: W/D/L (NULL until match complete)"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Timestamp when record was created"
    )

    # Relationships
    club = relationship("Club", back_populates="matches")
    opponent_club = relationship("OpponentClub", back_populates="matches")
    goals = relationship("Goal", back_populates="match", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="match", cascade="all, delete-orphan")
    match_statistics = relationship("MatchStatistics", back_populates="match", cascade="all, delete-orphan")
    player_match_statistics = relationship("PlayerMatchStatistics", back_populates="match", cascade="all, delete-orphan")
    lineups = relationship("MatchLineup", back_populates="match", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_matches_club_id", "club_id"),
        Index("idx_matches_match_date", "match_date"),
    )

    def __repr__(self):
        return f"<Match(match_id={self.match_id}, opponent_name='{self.opponent_name}', date={self.match_date})>"
