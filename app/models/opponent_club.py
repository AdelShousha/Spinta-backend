"""
Opponent club model for storing opponent team information.
"""
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.models.base import Base, GUID, generate_uuid


class OpponentClub(Base):
    """
    Opponent clubs are teams that play against our clubs.
    Not managed by our coaches, created automatically from match data.
    """
    __tablename__ = "opponent_clubs"

    opponent_club_id = Column(GUID, primary_key=True, default=generate_uuid)
    opponent_name = Column(String(255), nullable=False)
    statsbomb_team_id = Column(Integer, unique=True, nullable=True)
    logo_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    matches = relationship("Match", back_populates="opponent_club")
    opponent_players = relationship("OpponentPlayer", back_populates="opponent_club", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<OpponentClub(opponent_club_id={self.opponent_club_id}, opponent_name='{self.opponent_name}')>"
