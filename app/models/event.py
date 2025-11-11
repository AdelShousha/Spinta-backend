"""
Event model for storing raw StatsBomb event data.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.models.base import Base, GUID, generate_uuid


class Event(Base):
    """
    Stores raw StatsBomb event data with full JSON.
    Used to calculate player and match statistics.
    Indexed for efficient JSONB queries using GIN index.
    """
    __tablename__ = "events"

    event_id = Column(GUID, primary_key=True, default=generate_uuid)
    match_id = Column(GUID, ForeignKey("matches.match_id", ondelete="CASCADE"), nullable=False)
    statsbomb_player_id = Column(Integer, nullable=True)
    statsbomb_team_id = Column(Integer, nullable=True)
    player_name = Column(String(255), nullable=True)
    team_name = Column(String(255), nullable=True)
    event_type_name = Column(String(100), nullable=True)
    position_name = Column(String(50), nullable=True)
    minute = Column(Integer, nullable=True)
    second = Column(Integer, nullable=True)
    period = Column(Integer, nullable=True)
    event_data = Column(JSONB, nullable=True)  # Full event JSON for flexibility
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    match = relationship("Match", back_populates="events")

    def __repr__(self):
        return f"<Event(event_id={self.event_id}, event_type_name='{self.event_type_name}', player_name='{self.player_name}')>"


# Create GIN index on event_data for efficient JSONB queries
Index('idx_events_event_data', Event.event_data, postgresql_using='gin')
