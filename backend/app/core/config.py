"""
Application configuration — loads settings from .env file.
"""

import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class Settings:
    """Centralized application settings."""

    # Active AI Provider: "local", "groq", or "chatgpt"
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "groq" if os.getenv("GROQ_API_KEY") else ("local" if os.getenv("USE_LOCAL_AI", "True").lower() == "true" else "chatgpt"))

    # Local AI / Ollama Settings
    USE_LOCAL_AI: bool = os.getenv("USE_LOCAL_AI", "True").lower() == "true"
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

    # Groq Cloud LPU Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    # OpenAI Settings (fallback)
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

    # RAG Pipeline Tuning
    CHUNK_TARGET_SIZE: int = int(os.getenv("CHUNK_TARGET_SIZE", "3000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "1.5"))
    ENABLE_HYBRID_SEARCH: bool = os.getenv("ENABLE_HYBRID_SEARCH", "True").lower() == "true"


settings = Settings()


def set_ai_provider_setting(provider: str):
    """Updates in-memory settings and writes AI_PROVIDER and USE_LOCAL_AI to the root .env file on disk."""
    provider = provider.lower()
    if provider not in ("local", "groq", "chatgpt"):
        provider = "groq" if settings.GROQ_API_KEY else "local"

    settings.AI_PROVIDER = provider
    settings.USE_LOCAL_AI = (provider == "local")

    env_path = find_dotenv()
    if not env_path:
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
    
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            new_lines = []
            found_provider = False
            found_local = False
            for line in lines:
                if line.strip().startswith("AI_PROVIDER="):
                    new_lines.append(f"AI_PROVIDER={provider}\n")
                    found_provider = True
                elif line.strip().startswith("USE_LOCAL_AI="):
                    new_lines.append(f"USE_LOCAL_AI={settings.USE_LOCAL_AI}\n")
                    found_local = True
                else:
                    new_lines.append(line)
            
            if not found_provider:
                new_lines.append(f"AI_PROVIDER={provider}\n")
            if not found_local:
                new_lines.append(f"USE_LOCAL_AI={settings.USE_LOCAL_AI}\n")
                
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception as e:
            print(f"Warning: Failed to rewrite .env file: {e}")


def set_use_local_ai_setting(val: bool):
    """Legacy helper: Updates in-memory settings and writes USE_LOCAL_AI / AI_PROVIDER to disk."""
    provider = "local" if val else "chatgpt"
    set_ai_provider_setting(provider)


