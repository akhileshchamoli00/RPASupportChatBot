"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Chat Message Schemas
# ---------------------------------------------------------------------------

class ChatMessageRequest(BaseModel):
    """Incoming chat message from the user."""
    message: str


class ChatMessageResponse(BaseModel):
    """A single message returned to the client."""
    id: int
    session_id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Chat Session Schemas
# ---------------------------------------------------------------------------

class ChatSessionCreate(BaseModel):
    """Request body to create a new session."""
    title: Optional[str] = None


class ChatSessionResponse(BaseModel):
    """Session metadata returned to the client."""
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatSessionDetail(ChatSessionResponse):
    """Session with its full message history."""
    messages: list[ChatMessageResponse] = []


class SessionTitleUpdate(BaseModel):
    """Request body to rename a session."""
    title: str


# ---------------------------------------------------------------------------
# RAG Chat Response
# ---------------------------------------------------------------------------

class ChatResponse(BaseModel):
    """Full response returned after processing a user query."""
    session_id: str
    user_message: ChatMessageResponse
    ai_message: ChatMessageResponse
