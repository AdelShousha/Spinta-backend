"""
Match model for storing match records.
"""
from sqlalchemy import Column, String, Date, Time, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.models.base import Base, GUID, generate_uuid


class Match(Base):
    """
    Stores match records between our club and opponent clubs.
    Created by coaches uploading match videos with StatsBomb event data.
    """
    __tablename__ = "matches"

    match_id = Column(GUID, primary_key=True, default=generate_uuid)
    club_id = Column(GUID, ForeignKey("clubs.club_id", ondelete="CASCADE"), nullable=False)
    opponent_club_id = Column(GUID, ForeignKey("opponent_clubs.opponent_club_id", ondelete="SET NULL"), nullable=True)
    opponent_name = Column(String(255), nullable=False)  # Denormalized for easier queries
    match_date = Column(Date, nullable=False)
    match_time = Column(Time, nullable=True)
    is_home_match = Column(Boolean, nullable=False)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    club = relationship("Club", back_populates="matches")
    opponent_club = relationship("OpponentClub", back_populates="matches")
    goals = relationship("Goal", back_populates="match", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="match", cascade="all, delete-orphan")
    match_statistics = relationship("MatchStatistics", back_populates="match", cascade="all, delete-orphan")
    player_match_statistics = relationship("PlayerMatchStatistics", back_populates="match", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Match(match_id={self.match_id}, club_id={self.club_id}, opponent_name='{self.opponent_name}', date={self.match_date})>"
