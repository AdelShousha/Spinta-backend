"""
OpponentPlayer Model

Stores opponent team players for lineup display purposes.

Key Features:
- Linked to opponent clubs
- Basic info extracted from StatsBomb event data
- Used for displaying lineups in match views
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, generate_uuid
from datetime import datetime, timezone


class OpponentPlayer(Base):
    """
    Opponent Player Model

    Represents players from opponent teams.

    Attributes:
        opponent_player_id: Unique identifier for the opponent player
        opponent_club_id: Foreign key to opponent club (CASCADE on delete)
        player_name: Player name from event data
        statsbomb_player_id: StatsBomb's unique player identifier (nullable)
        jersey_number: Player's jersey number (nullable)
        position: Player position (nullable)
        created_at: Timestamp when record was created

    Relationships:
        - opponent_club: Many-to-one with OpponentClub model
    """

    __tablename__ = "opponent_players"

    # Primary key
    opponent_player_id = Column(
        GUID,
        primary_key=True,
        default=generate_uuid,
        comment="Unique identifier for the opponent player"
    )

    # Foreign key
    opponent_club_id = Column(
        GUID,
        ForeignKey("opponent_clubs.opponent_club_id", ondelete="CASCADE"),
        nullable=False,
        comment="Opponent club (CASCADE on deletion)"
    )

    # Player information
    player_name = Column(
        String(255),
        nullable=False,
        comment="Player name from event data"
    )

    statsbomb_player_id = Column(
        Integer,
        nullable=True,
        comment="StatsBomb player ID"
    )

    jersey_number = Column(
        Integer,
        nullable=True,
        comment="Player's jersey number"
    )

    position = Column(
        String(50),
        nullable=True,
        comment="Player position"
    )

    # Timestamp (created_at only, no updated_at)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Timestamp when record was created"
    )

    # Relationships
    opponent_club = relationship("OpponentClub", back_populates="opponent_players")

    def __repr__(self):
        return f"<OpponentPlayer(opponent_player_id={self.opponent_player_id}, player_name='{self.player_name}')>"
