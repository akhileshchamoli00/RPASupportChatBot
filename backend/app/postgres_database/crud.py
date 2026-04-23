"""
CRUD operations for chat sessions and messages.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.postgres_database.models import ChatSession, ChatMessage


# ---------------------------------------------------------------------------
# Chat Sessions
# ---------------------------------------------------------------------------

def create_session(db: Session, title: Optional[str] = None) -> ChatSession:
    """Create a new chat session."""
    session = ChatSession(title=title or "New Chat")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: str) -> Optional[ChatSession]:
    """Retrieve a chat session by ID."""
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()


def get_all_sessions(db: Session) -> list[ChatSession]:
    """Retrieve all chat sessions, most recent first."""
    return (
        db.query(ChatSession)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )


def update_session_title(db: Session, session_id: str, title: str) -> Optional[ChatSession]:
    """Update the title of a chat session."""
    session = get_session(db, session_id)
    if session:
        session.title = title
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
    return session


def delete_session(db: Session, session_id: str) -> bool:
    """Delete a chat session and all its messages."""
    session = get_session(db, session_id)
    if session:
        db.delete(session)
        db.commit()
        return True
    return False


# ---------------------------------------------------------------------------
# Chat Messages
# ---------------------------------------------------------------------------

def add_message(db: Session, session_id: str, role: str, content: str) -> ChatMessage:
    """Add a message to a chat session."""
    message = ChatMessage(session_id=session_id, role=role, content=content)
    db.add(message)
    # Also bump the session's updated_at timestamp
    session = get_session(db, session_id)
    if session:
        session.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(message)
    return message


def get_session_messages(db: Session, session_id: str) -> list[ChatMessage]:
    """Get all messages for a given session, ordered by creation time."""
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
