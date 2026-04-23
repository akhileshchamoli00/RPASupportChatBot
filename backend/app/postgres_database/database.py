"""
SQLAlchemy database engine and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# Create the SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL, echo=False)

# Session factory — each request gets its own session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a database session.
    Automatically closes the session when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
