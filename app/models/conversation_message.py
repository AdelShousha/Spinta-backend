"""
ConversationMessage Model

Stores chat messages for the AI chatbot feature.

Key Features:
- Session-based conversations (grouped by session_id)
- Access control via user_id and club_id
- Stores tool calls and results in JSONB
- Indexed for efficient history retrieval
"""

from sqlalchemy import Column, String, DateTime, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone

from app.models.base import Base, GUID, generate_uuid


class ConversationMessage(Base):
    """
    Conversation Message Model

    Stores individual messages in chatbot conversations.

    Attributes:
        id: Unique message identifier
        session_id: Groups messages into conversations
        user_id: Owner of the conversation (FK to users)
        club_id: Club context for data access (FK to clubs)
        role: Message author ('user', 'assistant', 'system')
        content: Message text content
        tool_calls: JSONB storing function calls and results
        timestamp: When message was created

    Indexes:
        - session_id: For filtering messages by session
        - user_id: For access control queries
        - club_id: For club-scoped queries
        - timestamp: For ordering messages
        - (session_id, timestamp): Composite for efficient history retrieval
    """

    __tablename__ = "conversation_messages"

    # Primary key
    id = Column(
        GUID,
        primary_key=True,
        default=generate_uuid,
        comment="Unique message identifier"
    )

    # Session grouping
    session_id = Column(
        GUID,
        nullable=False,
        index=True,
        comment="Groups messages into conversations"
    )

    # Access control - Foreign keys to existing tables
    user_id = Column(
        GUID,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner of the conversation"
    )

    club_id = Column(
        GUID,
        ForeignKey("clubs.club_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Club context for data access"
    )

    # Message data
    role = Column(
        String(20),
        nullable=False,
        comment="Message author: 'user', 'assistant', or 'system'"
    )

    content = Column(
        Text,
        nullable=False,
        comment="Message text content"
    )

    # Tool calls storage (for function calling)
    tool_calls = Column(
        JSONB,
        nullable=True,
        comment="Stores function calls and results as JSON"
    )

    # Timestamp
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
        comment="When message was created"
    )

    # Composite index for efficient history queries
    __table_args__ = (
        Index('idx_conversation_session_timestamp', 'session_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<ConversationMessage(id={self.id}, session={self.session_id}, role={self.role})>"
