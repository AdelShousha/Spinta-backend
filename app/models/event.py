"""
Event Model

Stores raw StatsBomb event data from matches.

Key Features:
- Stores full event JSON for flexibility
- JSONB for PostgreSQL (efficient querying with GIN index)
- JSON for SQLite (testing compatibility)
- Used to calculate player and match statistics
- Links to players via statsbomb_player_id
"""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Index, func, TypeDecorator, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base, GUID, generate_uuid
from datetime import datetime, timezone
import json


class JSONBType(TypeDecorator):
    """
    Platform-independent JSONB type.

    Uses PostgreSQL's JSONB type when available (efficient with GIN index),
    otherwise uses Text for SQLite (testing).

    This allows our models to work with both PostgreSQL (production)
    and SQLite (testing) without changes.

    Technical Details:
    - PostgreSQL: Stores as native JSONB type (efficient, indexed)
    - SQLite: Stores as Text (compatible)
    - Python: Always works with dicts/lists
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """
        Return appropriate type for the dialect.

        Args:
            dialect: SQLAlchemy dialect (postgresql, sqlite, etc.)

        Returns:
            JSONB for PostgreSQL, Text for others
        """
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        """
        Process value before sending to database.

        Args:
            value: The dict/list value or None
            dialect: The database dialect

        Returns:
            For PostgreSQL: dict/list (handled by JSONB)
            For SQLite: JSON string
        """
        if value is None:
            return value

        if dialect.name == 'postgresql':
            return value  # PostgreSQL JSONB handles dict directly
        else:
            return json.dumps(value)  # SQLite needs string

    def process_result_value(self, value, dialect):
        """
        Process value coming from database.

        Args:
            value: The value from database
            dialect: The database dialect

        Returns:
            dict/list or None
        """
        if value is None:
            return value

        if dialect.name == 'postgresql':
            return value  # PostgreSQL returns dict already
        else:
            return json.loads(value)  # SQLite returns string


class Event(Base):
    """
    Event Model

    Represents a single event from StatsBomb match data.

    Attributes:
        event_id: Unique identifier for the event
        match_id: Foreign key to match (CASCADE on delete)
        statsbomb_player_id: StatsBomb player ID (nullable)
        statsbomb_team_id: StatsBomb team ID (nullable)
        player_name: Player name from event (nullable)
        team_name: Team name from event (nullable)
        event_type_name: Event type (Pass, Shot, etc.)
        position_name: Player position (nullable)
        minute: Match minute (nullable)
        second: Second within minute (nullable)
        period: Match period (nullable)
        event_data: Full event JSON data (JSONB/JSON)
        created_at: Timestamp when record was created

    Relationships:
        - match: Many-to-one with Match model
    """

    __tablename__ = "events"

    # Primary key
    event_id = Column(
        GUID,
        primary_key=True,
        default=generate_uuid,
        comment="Unique event identifier"
    )

    # Foreign key
    match_id = Column(
        GUID,
        ForeignKey("matches.match_id", ondelete="CASCADE"),
        nullable=False,
        comment="Match reference (CASCADE on deletion)"
    )

    # StatsBomb identifiers
    statsbomb_player_id = Column(
        Integer,
        nullable=True,
        comment="StatsBomb player ID"
    )

    statsbomb_team_id = Column(
        Integer,
        nullable=True,
        comment="StatsBomb team ID"
    )

    # Event information
    player_name = Column(
        String(255),
        nullable=True,
        comment="Player name from event"
    )

    team_name = Column(
        String(255),
        nullable=True,
        comment="Team name from event"
    )

    event_type_name = Column(
        String(100),
        nullable=True,
        comment="Event type (Pass, Shot, etc.)"
    )

    position_name = Column(
        String(50),
        nullable=True,
        comment="Player position"
    )

    minute = Column(
        Integer,
        nullable=True,
        comment="Match minute"
    )

    second = Column(
        Integer,
        nullable=True,
        comment="Second within minute"
    )

    period = Column(
        Integer,
        nullable=True,
        comment="Match period"
    )

    # Full event JSON data
    event_data = Column(
        JSONBType,
        nullable=True,
        comment="Full event JSON data (JSONB in PostgreSQL, JSON in SQLite)"
    )

    # Timestamp (created_at only, no updated_at)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Timestamp when record was created"
    )

    # Relationships
    match = relationship("Match")

    # Indexes
    # Note: GIN index on event_data is PostgreSQL-specific, created in migration
    __table_args__ = (
        Index("idx_events_match_id", "match_id"),
        Index("idx_events_statsbomb_player_id", "statsbomb_player_id"),
        Index("idx_events_event_type_name", "event_type_name"),
    )

    def __repr__(self):
        return f"<Event(event_id={self.event_id}, type='{self.event_type_name}', player='{self.player_name}')>"
