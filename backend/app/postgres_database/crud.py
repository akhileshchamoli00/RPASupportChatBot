"""
CRUD operations for chat sessions and messages.
"""

import bcrypt
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.postgres_database.models import User, ChatSession, ChatMessage


# ---------------------------------------------------------------------------
# User Authentication CRUD
# ---------------------------------------------------------------------------

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Find a user by their username."""
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, username: str, password: str) -> User:
    """Create a new user with a bcrypt hashed password."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(username=username, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if the provided password matches the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Chat Sessions
# ---------------------------------------------------------------------------

def create_session(
    db: Session,
    title: Optional[str] = None,
    automation: Optional[str] = None,
    user_id: Optional[str] = None,
) -> ChatSession:
    """Create a new chat session linked to a specific user."""
    session = ChatSession(title=title or "New Chat", automation=automation, user_id=user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: str, user_id: Optional[str] = None) -> Optional[ChatSession]:
    """Retrieve a chat session by ID, optionally verifying ownership."""
    query = db.query(ChatSession).filter(ChatSession.id == session_id)
    if user_id:
        query = query.filter(ChatSession.user_id == user_id)
    return query.first()


def get_all_sessions(db: Session, user_id: Optional[str] = None) -> list[ChatSession]:
    """Retrieve all chat sessions for a specific user, most recent first."""
    query = db.query(ChatSession)
    if user_id:
        query = query.filter(ChatSession.user_id == user_id)
    return query.order_by(ChatSession.updated_at.desc()).all()


def update_session_title(db: Session, session_id: str, title: str, user_id: Optional[str] = None) -> Optional[ChatSession]:
    """Update the title of a chat session."""
    session = get_session(db, session_id, user_id=user_id)
    if session:
        session.title = title
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
    return session


def update_session_automation(db: Session, session_id: str, automation: str, user_id: Optional[str] = None) -> Optional[ChatSession]:
    """Update the automation workspace of a chat session."""
    session = get_session(db, session_id, user_id=user_id)
    if session:
        session.automation = automation
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
    return session


def delete_session(db: Session, session_id: str, user_id: Optional[str] = None) -> bool:
    """Delete a chat session and all its messages."""
    session = get_session(db, session_id, user_id=user_id)
    if session:
        db.delete(session)
        db.commit()
        return True
    return False


# ---------------------------------------------------------------------------
# Chat Messages
# ---------------------------------------------------------------------------

def add_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
    model_used: Optional[str] = None,
    sources_json: Optional[str] = None,
) -> ChatMessage:
    """Add a message to a chat session with optional token usage tracking and sources JSON."""
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        model_used=model_used,
        sources_json=sources_json,
    )
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
