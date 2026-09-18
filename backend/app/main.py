"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from app.postgres_database.database import engine, Base
from app.api.routes.chat import router as chat_router
from app.api.routes.auth import router as auth_router

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

import bcrypt

# Ensure new token tracking columns and user isolation exist on existing tables
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS prompt_tokens integer DEFAULT 0;"))
        conn.execute(text("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS completion_tokens integer DEFAULT 0;"))
        conn.execute(text("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS total_tokens integer DEFAULT 0;"))
        conn.execute(text("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS model_used character varying(100);"))
        conn.execute(text("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS sources_json text;"))
        conn.execute(text("ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS user_id character varying(100);"))
        conn.execute(text("UPDATE chat_sessions SET user_id = 'akhilesh' WHERE user_id IS NULL;"))

        # Pre-seed default account for testing if not exists
        existing = conn.execute(text("SELECT id FROM users WHERE username = 'akhilesh'")).first()
        if not existing:
            hashed = bcrypt.hashpw("password".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            conn.execute(
                text("INSERT INTO users (username, hashed_password) VALUES (:u, :p)"),
                {"u": "akhilesh", "p": hashed}
            )
except Exception as mig_err:
    print(f"Schema update notice: {mig_err}")

# Initialize FastAPI app
app = FastAPI(
    title="Dayforce Automation Atlas",
    description="RAG-powered chatbot API for Dayforce Automation Atlas",
    version="1.0.0",
)

# CORS — allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth_router)
app.include_router(chat_router)


@app.get("/", tags=["Health"])
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "Dayforce Automation Atlas"}

