"""
Application configuration — loads settings from .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Centralized application settings."""

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    CHAT_MODEL: str = os.getenv("CHAT_MODEL", "gpt-4o")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    TOP_K: int = int(os.getenv("TOP_K", "5"))

    # PostgreSQL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/dayforce_rpasupport_assistant_db",
    )

    # ChromaDB
    CHROMA_COLLECTION_NAME: str = os.getenv(
        "CHROMA_COLLECTION_NAME", "dayforce_rpasupport_assistant_db"
    )
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./vector_db")


settings = Settings()
