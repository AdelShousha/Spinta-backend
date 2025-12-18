"""
Chat Schemas

Pydantic models for chatbot API request/response validation.

Note: user_id and club_id are NOT in ChatMessageRequest because
they come from the authenticated coach via JWT token.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class ChatMessageRequest(BaseModel):
    """
    Request model for sending a chat message.

    Note: user_id and club_id come from JWT authentication,
    not from the request body.
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User message to send to the chatbot"
    )
    session_id: Optional[UUID] = Field(
        None,
        description="Session ID for continuing a conversation. Creates new session if not provided."
    )


class ToolCallInfo(BaseModel):
    """Information about a tool call executed during the conversation."""
    tool_name: str = Field(..., description="Name of the tool that was called")
    arguments: Dict[str, Any] = Field(..., description="Arguments passed to the tool")
    result: Optional[Any] = Field(None, description="Result returned by the tool")


class ChatMessageResponse(BaseModel):
    """Response model for chat message."""
    session_id: UUID = Field(..., description="Session ID for continuing the conversation")
    message: str = Field(..., description="Assistant's response message")
    tool_calls_executed: List[str] = Field(
        default_factory=list,
        description="Names of tools that were called to answer the query"
    )
    timestamp: datetime = Field(..., description="When the response was generated")

    model_config = {"from_attributes": True}


class ChatSessionResponse(BaseModel):
    """Response model for creating a new chat session."""
    session_id: UUID = Field(..., description="Unique session identifier")
    created_at: datetime = Field(..., description="When the session was created")


class ConversationHistoryItem(BaseModel):
    """Single message in conversation history."""
    role: str = Field(..., description="Message author: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Tool calls executed for this message (assistant messages only)"
    )
    timestamp: datetime = Field(..., description="When the message was created")


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history."""
    session_id: UUID = Field(..., description="Session identifier")
    messages: List[ConversationHistoryItem] = Field(..., description="List of messages in the conversation")
    total_messages: int = Field(..., description="Total number of messages in the session")


class ClearSessionResponse(BaseModel):
    """Response model for clearing a chat session."""
    message: str = Field(..., description="Success message")
    deleted_messages: int = Field(..., description="Number of messages deleted")
