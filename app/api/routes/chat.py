"""
Chat API Endpoints

Chatbot endpoints for coaches with JWT authentication.
Uses Gemini AI with function calling for database queries.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone

from app.database import get_db
from app.core.dependencies import require_coach
from app.models.user import User
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionResponse,
    ConversationHistoryResponse,
    ConversationHistoryItem,
    ClearSessionResponse
)
from app.services.chatbot.conversation_service import ConversationService
from app.services.chatbot.llm_service import LLMService


router = APIRouter()

# Service instances
conversation_service = ConversationService()


def get_llm_service():
    """Get or create LLM service instance."""
    return LLMService()


def get_coach_context(coach: User) -> tuple[UUID, UUID]:
    """
    Extract user_id and club_id from authenticated coach.

    Args:
        coach: Authenticated coach user

    Returns:
        Tuple of (user_id, club_id)

    Raises:
        HTTPException: If coach doesn't have an associated club
    """
    if not coach.coach or not coach.coach.club:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coach does not have an associated club. Please create a club first."
        )

    return coach.user_id, coach.coach.club.club_id


@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new chat session"
)
def create_chat_session(
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db)
):
    """
    Create a new chat session for the authenticated coach.

    Returns:
        Session information with session_id and created_at timestamp
    """
    user_id, club_id = get_coach_context(coach)

    session_id = conversation_service.create_session(
        db=db,
        user_id=user_id,
        club_id=club_id
    )

    return ChatSessionResponse(
        session_id=session_id,
        created_at=datetime.now(timezone.utc)
    )


@router.post(
    "/messages",
    response_model=ChatMessageResponse,
    summary="Send chat message"
)
def send_message(
    request: ChatMessageRequest,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db)
):
    """
    Send a message to the AI chatbot.

    Creates a new session if session_id is not provided.
    The AI will analyze the query and use appropriate database tools
    to provide data-driven responses about players, matches, and team stats.

    Args:
        request: Chat message request with message and optional session_id

    Returns:
        AI response with session_id and list of tools executed
    """
    user_id, club_id = get_coach_context(coach)

    # Determine session ID
    if request.session_id:
        session_id = request.session_id
        # Verify session exists and belongs to this user
        if not conversation_service.session_exists(
            db=db,
            session_id=session_id,
            user_id=user_id,
            club_id=club_id
        ):
            # Create new session with provided ID
            session_id = conversation_service.create_session(
                db=db,
                user_id=user_id,
                club_id=club_id
            )
    else:
        # Create new session
        session_id = conversation_service.create_session(
            db=db,
            user_id=user_id,
            club_id=club_id
        )

    # Get conversation history
    history = conversation_service.get_conversation_history(
        db=db,
        session_id=session_id,
        user_id=user_id,
        club_id=club_id
    )

    # Filter out system messages for LLM context
    llm_history = [msg for msg in history if msg["role"] != "system"]

    # Save user message
    conversation_service.add_message(
        db=db,
        session_id=session_id,
        user_id=user_id,
        club_id=club_id,
        role="user",
        content=request.message
    )

    # Get LLM response with function calling
    try:
        llm_service = get_llm_service()
        llm_response = llm_service.chat(
            user_message=request.message,
            conversation_history=llm_history,
            db=db,
            club_id=club_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )

    # Save assistant response
    conversation_service.add_message(
        db=db,
        session_id=session_id,
        user_id=user_id,
        club_id=club_id,
        role="assistant",
        content=llm_response["message"],
        tool_calls=llm_response.get("tool_results")
    )

    return ChatMessageResponse(
        session_id=session_id,
        message=llm_response["message"],
        tool_calls_executed=llm_response["tool_calls_executed"],
        timestamp=datetime.now(timezone.utc)
    )


@router.get(
    "/sessions/{session_id}/messages",
    response_model=ConversationHistoryResponse,
    summary="Get conversation history"
)
def get_conversation_history(
    session_id: UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db)
):
    """
    Get conversation history for a specific session.

    Args:
        session_id: Chat session ID

    Returns:
        List of messages in the conversation
    """
    user_id, club_id = get_coach_context(coach)

    history = conversation_service.get_conversation_history(
        db=db,
        session_id=session_id,
        user_id=user_id,
        club_id=club_id
    )

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or no messages"
        )

    return ConversationHistoryResponse(
        session_id=session_id,
        messages=[
            ConversationHistoryItem(
                role=msg["role"],
                content=msg["content"],
                tool_calls=msg.get("tool_calls"),
                timestamp=msg["timestamp"]
            )
            for msg in history
        ],
        total_messages=len(history)
    )


@router.delete(
    "/sessions/{session_id}",
    response_model=ClearSessionResponse,
    summary="Clear chat session"
)
def clear_chat_session(
    session_id: UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db)
):
    """
    Clear all messages in a chat session.

    Args:
        session_id: Chat session ID to clear

    Returns:
        Success message with count of deleted messages
    """
    user_id, club_id = get_coach_context(coach)

    deleted_count = conversation_service.clear_session(
        db=db,
        session_id=session_id,
        user_id=user_id,
        club_id=club_id
    )

    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return ClearSessionResponse(
        message="Session cleared successfully",
        deleted_messages=deleted_count
    )
