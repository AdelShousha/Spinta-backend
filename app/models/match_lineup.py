"""
MatchLineup Model

Stores lineup information for both teams in a match.

Key Features:
- Tracks which players participated in a match
- Supports both our team players and opponent players
- Denormalized player information for easier queries
- Created during match data import from StatsBomb
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Index, CheckConstraint, func
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, generate_uuid


class MatchLineup(Base):
    """
    MatchLineup Model

    Represents a player in a match lineup (for either our team or opponent team).

    Attributes:
        lineup_id: Unique identifier for the lineup entry
        match_id: Foreign key to match (CASCADE on delete)
        team_type: 'our_team' or 'opponent_team'
        player_id: Foreign key to our players (CASCADE on delete, nullable)
        opponent_player_id: Foreign key to opponent players (CASCADE on delete, nullable)
        player_name: Denormalized player name for easier queries
        jersey_number: Player's jersey number in this match
        position: Player's position in this match
        created_at: Timestamp when record was created

    Relationships:
        - match: Many-to-one with Match model
        - player: Many-to-one with Player model (for our team)
        - opponent_player: Many-to-one with OpponentPlayer model (for opponent team)

    Constraints:
        - team_type must be 'our_team' or 'opponent_team'
        - For our_team: player_id must be set, opponent_player_id must be NULL
        - For opponent_team: opponent_player_id must be set, player_id must be NULL
    """

    __tablename__ = "match_lineups"

    # Primary key
    lineup_id = Column(
        GUID,
        primary_key=True,
        default=generate_uuid,
        comment="Unique lineup entry identifier"
    )

    # Foreign key to match
    match_id = Column(
        GUID,
        ForeignKey("matches.match_id", ondelete="CASCADE"),
        nullable=False,
        comment="Match reference (CASCADE on deletion)"
    )

    # Team type
    team_type = Column(
        String(20),
        nullable=False,
        comment="Team type: 'our_team' or 'opponent_team'"
    )

    # Foreign key to our player (nullable - only for our team)
    player_id = Column(
        GUID,
        ForeignKey("players.player_id", ondelete="CASCADE"),
        nullable=True,
        comment="Our player reference (CASCADE on deletion, NULL for opponent)"
    )

    # Foreign key to opponent player (nullable - only for opponent team)
    opponent_player_id = Column(
        GUID,
        ForeignKey("opponent_players.opponent_player_id", ondelete="CASCADE"),
        nullable=True,
        comment="Opponent player reference (CASCADE on deletion, NULL for our team)"
    )

    # Denormalized player information
    player_name = Column(
        String(255),
        nullable=False,
        comment="Player name (denormalized)"
    )

    jersey_number = Column(
        Integer,
        nullable=False,
        comment="Jersey number in this match"
    )

    position = Column(
        String(50),
        nullable=False,
        comment="Player position in this match"
    )

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when record was created"
    )

    # Relationships
    match = relationship("Match", back_populates="lineups")
    player = relationship("Player")
    opponent_player = relationship("OpponentPlayer")

    # Indexes and constraints
    __table_args__ = (
        Index("idx_match_lineups_match_id", "match_id"),
        Index("idx_match_lineups_player_id", "player_id"),
        Index("idx_match_lineups_opponent_player_id", "opponent_player_id"),
        CheckConstraint(
            "team_type IN ('our_team', 'opponent_team')",
            name="check_team_type"
        ),
    )

    def __repr__(self):
        return f"<MatchLineup(lineup_id={self.lineup_id}, player_name='{self.player_name}', team_type='{self.team_type}')>"
