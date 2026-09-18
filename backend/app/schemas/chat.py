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
    ai_provider: Optional[str] = None
    use_local_ai: Optional[bool] = None


class AISettingsResponse(BaseModel):
    """Current AI Provider Settings."""
    ai_provider: str
    use_local_ai: bool
    chat_model: str
    local_model: str = "llama3.1:8b"
    groq_model: str = "qwen/qwen3.8-27b"
    cloud_model: str = "gpt-4o-mini"
    has_groq_key: bool = False
    has_openai_key: bool = False


class AISettingsUpdate(BaseModel):
    """Request to update AI Provider setting."""
    ai_provider: Optional[str] = None
    use_local_ai: Optional[bool] = None



class ChatMessageResponse(BaseModel):
    """A single message returned to the client."""
    id: int
    session_id: str
    role: str
    content: str
    created_at: datetime
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    model_used: Optional[str] = None
    sources: Optional[list[dict]] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Chat Session Schemas
# ---------------------------------------------------------------------------

class ChatSessionCreate(BaseModel):
    """Request body to create a new session."""
    title: Optional[str] = None
    automation: Optional[str] = None
    user_id: Optional[str] = None


class ChatSessionResponse(BaseModel):
    """Session metadata returned to the client."""
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    automation: Optional[str] = None
    user_id: Optional[str] = None

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
    sources: Optional[list[dict]] = []
    token_usage: Optional[dict] = None
