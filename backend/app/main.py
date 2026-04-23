"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.postgres_database.database import engine, Base
from app.api.routes.chat import router as chat_router
from app.api.routes.auth import router as auth_router

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Dayforce RPA Support Assistant",
    description="RAG-powered chatbot API for Dayforce RPA support",
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
    return {"status": "ok", "service": "Dayforce RPA Support Assistant"}
