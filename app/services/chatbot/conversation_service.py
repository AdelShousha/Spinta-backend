"""
Conversation Management Service

Synchronous service for managing chat conversation history in PostgreSQL.
"""

from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.models.conversation_message import ConversationMessage


class ConversationService:
    """Service for managing conversation history in PostgreSQL."""

    @staticmethod
    def create_session(
        db: Session,
        user_id: UUID,
        club_id: UUID
    ) -> UUID:
        """
        Create a new chat session.

        Args:
            db: Database session
            user_id: User ID
            club_id: Club ID

        Returns:
            New session ID
        """
        session_id = uuid4()

        # Create initial system message
        system_message = ConversationMessage(
            session_id=session_id,
            user_id=user_id,
            club_id=club_id,
            role="system",
            content="You are an AI assistant for Spinta Stats, helping coaches analyze soccer data.",
            timestamp=datetime.now(timezone.utc)
        )

        db.add(system_message)
        db.commit()

        return session_id

    @staticmethod
    def add_message(
        db: Session,
        session_id: UUID,
        user_id: UUID,
        club_id: UUID,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> ConversationMessage:
        """
        Add a message to the conversation history.

        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID
            club_id: Club ID
            role: Message role ('user' or 'assistant')
            content: Message content
            tool_calls: Optional tool calls data

        Returns:
            Created message
        """
        message = ConversationMessage(
            session_id=session_id,
            user_id=user_id,
            club_id=club_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            timestamp=datetime.now(timezone.utc)
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        return message

    @staticmethod
    def get_conversation_history(
        db: Session,
        session_id: UUID,
        user_id: UUID,
        club_id: UUID,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.

        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID (for access control)
            club_id: Club ID (for access control)
            limit: Optional limit on number of messages

        Returns:
            List of messages in chronological order
        """
        query = (
            select(ConversationMessage)
            .where(
                ConversationMessage.session_id == str(session_id),
                ConversationMessage.user_id == str(user_id),
                ConversationMessage.club_id == str(club_id)
            )
            .order_by(ConversationMessage.timestamp)
        )

        if limit:
            query = query.limit(limit)

        result = db.execute(query)
        messages = result.scalars().all()

        return [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "tool_calls": msg.tool_calls,
                "timestamp": msg.timestamp
            }
            for msg in messages
        ]

    @staticmethod
    def clear_session(
        db: Session,
        session_id: UUID,
        user_id: UUID,
        club_id: UUID
    ) -> int:
        """
        Clear all messages in a session.

        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID (for access control)
            club_id: Club ID (for access control)

        Returns:
            Number of messages deleted
        """
        query = delete(ConversationMessage).where(
            ConversationMessage.session_id == str(session_id),
            ConversationMessage.user_id == str(user_id),
            ConversationMessage.club_id == str(club_id)
        )

        result = db.execute(query)
        db.commit()

        return result.rowcount

    @staticmethod
    def session_exists(
        db: Session,
        session_id: UUID,
        user_id: UUID,
        club_id: UUID
    ) -> bool:
        """
        Check if a session exists and belongs to the user.

        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID
            club_id: Club ID

        Returns:
            True if session exists, False otherwise
        """
        query = (
            select(ConversationMessage)
            .where(
                ConversationMessage.session_id == str(session_id),
                ConversationMessage.user_id == str(user_id),
                ConversationMessage.club_id == str(club_id)
            )
            .limit(1)
        )

        result = db.execute(query)
        message = result.scalar_one_or_none()

        return message is not None
