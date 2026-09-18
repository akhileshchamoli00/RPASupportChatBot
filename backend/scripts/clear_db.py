import sys
import os

# Add backend root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.postgres_database.database import engine, Base
from app.postgres_database.models import ChatSession, ChatMessage

def clear_db():
    print("Connecting to PostgreSQL database...")
    print("Dropping existing tables: chat_messages, chat_sessions...")
    Base.metadata.drop_all(bind=engine)
    
    print("Recreating database tables with clean schemas...")
    Base.metadata.create_all(bind=engine)
    print("Database tables cleared and recreated successfully!")

if __name__ == "__main__":
    clear_db()
