"""
OpponentClub Model

Stores opponent team information (teams not managed by our coaches).
Created automatically when processing match event data from StatsBomb.

Key Features:
- Basic info only (name, logo, StatsBomb ID)
- Not linked to user accounts
- statsbomb_team_id is unique for StatsBomb integration
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, func
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, generate_uuid


class OpponentClub(Base):
    """
    Opponent Club Model

    Represents external teams that our club plays against.

    Attributes:
        opponent_club_id: Unique identifier for the opponent club
        opponent_name: Name of the opponent team
        statsbomb_team_id: StatsBomb's unique team identifier (nullable, unique)
        logo_url: URL to the opponent's logo image (nullable)
        created_at: Timestamp when the record was created

    Relationships:
        - matches: One-to-many with Match model
        - opponent_players: One-to-many with OpponentPlayer model
    """

    __tablename__ = "opponent_clubs"

    # Primary key
    opponent_club_id = Column(
        GUID,
        primary_key=True,
        default=generate_uuid,
        comment="Unique identifier for the opponent club"
    )

    # Basic information
    opponent_name = Column(
        String(255),
        nullable=False,
        comment="Name of the opponent team"
    )

    statsbomb_team_id = Column(
        Integer,
        unique=True,
        nullable=True,
        comment="StatsBomb's unique team identifier"
    )

    logo_url = Column(
        Text,
        nullable=True,
        comment="URL to the opponent's logo image"
    )

    # Timestamp (created_at only, no updated_at)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when record was created"
    )

    # Relationships
    matches = relationship("Match", back_populates="opponent_club", cascade="all, delete-orphan")
    opponent_players = relationship("OpponentPlayer", back_populates="opponent_club", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<OpponentClub(opponent_club_id={self.opponent_club_id}, opponent_name='{self.opponent_name}')>"
