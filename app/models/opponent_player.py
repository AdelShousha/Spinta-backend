"""
Opponent player model for storing opponent team players.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.models.base import Base, GUID, generate_uuid


class OpponentPlayer(Base):
    """
    Stores opponent team players for lineup display purposes.
    Created automatically from Starting XI events in match data.
    No individual statistics tracked (only team-level stats).
    """
    __tablename__ = "opponent_players"

    opponent_player_id = Column(GUID, primary_key=True, default=generate_uuid)
    opponent_club_id = Column(GUID, ForeignKey("opponent_clubs.opponent_club_id", ondelete="CASCADE"), nullable=False)
    player_name = Column(String(255), nullable=False)
    statsbomb_player_id = Column(Integer, nullable=True)
    jersey_number = Column(Integer, nullable=True)
    position = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    opponent_club = relationship("OpponentClub", back_populates="opponent_players")

    def __repr__(self):
        return f"<OpponentPlayer(opponent_player_id={self.opponent_player_id}, player_name='{self.player_name}', jersey_number={self.jersey_number})>"
