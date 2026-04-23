"""
Script to build the ChromaDB vector database from an Excel file.

Usage:
    cd backend
    python -m scripts.build_vector_db

The script reads the Excel file at documentation/test.xlsx,
extracts text from each row, generates embeddings via OpenAI,
and stores them in a persistent ChromaDB collection.
"""

import os
import sys

# Ensure the backend directory is on the path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import openpyxl
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./vector_db")
CHROMA_COLLECTION_NAME = os.getenv(
    "CHROMA_COLLECTION_NAME", "dayforce_rpasupport_assistant_db"
)
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "documentation", "test.xlsx")

# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------
openai_client = OpenAI(api_key=OPENAI_API_KEY)
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)


def generate_embedding(text: str) -> list[float]:
    """Generate an embedding for the given text."""
    response = openai_client.embeddings.create(input=text, model=EMBEDDING_MODEL)
    return response.data[0].embedding


def load_documents_from_excel(filepath: str) -> list[dict]:
    """
    Read the Excel file and return a list of documents.
    
    Assumes:
      - Row 1 is the header row.
      - All columns are concatenated into a single text block per row.
      - Each row becomes one document.
    """
    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        print("Excel file is empty.")
        return []

    headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(rows[0])]
    documents = []

    for row_idx, row in enumerate(rows[1:], start=2):
        # Build a readable text block from the row
        parts = []
        for header, value in zip(headers, row):
            if value is not None and str(value).strip():
                parts.append(f"{header}: {str(value).strip()}")

        if parts:
            text = "\n".join(parts)
            documents.append({"id": f"doc_{row_idx}", "text": text})

    return documents


def build_vector_db():
    """Main function: load docs, embed, store in ChromaDB."""
    print(f"Loading documents from: {os.path.abspath(EXCEL_PATH)}")
    documents = load_documents_from_excel(EXCEL_PATH)

    if not documents:
        print("No documents found. Exiting.")
        return

    print(f"Found {len(documents)} documents.")

    # Get or create the collection
    collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)

    # Process in batches to avoid rate limits
    batch_size = 20
    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        ids = [doc["id"] for doc in batch]
        texts = [doc["text"] for doc in batch]

        print(f"Embedding batch {i // batch_size + 1} ({len(batch)} docs)...")
        embeddings = []
        for text in texts:
            emb = generate_embedding(text)
            embeddings.append(emb)

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
        )

    print(
        f"Done! Collection '{CHROMA_COLLECTION_NAME}' now has "
        f"{collection.count()} documents."
    )


if __name__ == "__main__":
    build_vector_db()
