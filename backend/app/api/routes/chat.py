"""
FastAPI routes for the chat API.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.postgres_database.database import get_db
from app.postgres_database import crud
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionDetail,
    SessionTitleUpdate,
)
from app.services.rag_service import generate_chat_response

router = APIRouter(prefix="/api/chat", tags=["Chat"])


# ---------------------------------------------------------------------------
# Session endpoints
# ---------------------------------------------------------------------------

@router.post("/sessions", response_model=ChatSessionResponse)
def create_session(body: ChatSessionCreate, db: Session = Depends(get_db)):
    """Create a new chat session."""
    session = crud.create_session(db, title=body.title)
    return session


@router.get("/sessions", response_model=list[ChatSessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    """List all chat sessions (most recent first)."""
    return crud.get_all_sessions(db)


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get a session with its full message history."""
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.put("/sessions/{session_id}/title", response_model=ChatSessionResponse)
def rename_session(
    session_id: str, body: SessionTitleUpdate, db: Session = Depends(get_db)
):
    """Rename a chat session."""
    session = crud.update_session_title(db, session_id, body.title)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a chat session and all its messages."""
    deleted = crud.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"detail": "Session deleted"}


# ---------------------------------------------------------------------------
# Chat / RAG endpoint
# ---------------------------------------------------------------------------

@router.post("/sessions/{session_id}/message", response_model=ChatResponse)
def send_message(
    session_id: str,
    body: ChatMessageRequest,
    db: Session = Depends(get_db),
):
    """
    Send a user message, run the RAG pipeline, and return both the
    saved user message and the AI-generated response.
    """
    # Verify session exists
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save the user's message
    user_msg = crud.add_message(db, session_id, role="user", content=body.message)

    # Build conversation history from prior messages (for context continuity)
    prior_messages = crud.get_session_messages(db, session_id)
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in prior_messages
        if msg.id != user_msg.id  # exclude the message we just added
    ]

    # Run RAG pipeline
    try:
        ai_response_text = generate_chat_response(
            user_query=body.message,
            conversation_history=conversation_history,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    # Save the AI response
    ai_msg = crud.add_message(db, session_id, role="assistant", content=ai_response_text)

    # Auto-title the session on the first message
    if len(prior_messages) <= 1:
        # Use the first ~50 chars of the user's message as a title
        auto_title = body.message[:50] + ("..." if len(body.message) > 50 else "")
        crud.update_session_title(db, session_id, auto_title)

    return ChatResponse(
        session_id=session_id,
        user_message=ChatMessageResponse.model_validate(user_msg),
        ai_message=ChatMessageResponse.model_validate(ai_msg),
    )
