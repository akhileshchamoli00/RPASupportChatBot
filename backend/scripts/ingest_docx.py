"""
Script to ingest document files (.docx, .xlsx, .pdf) into the ChromaDB vector database.
Supports structure-aware chunking, PDF parsing, enriched metadata, and incremental SHA-256 indexing.

Usage:
    cd backend
    python -m scripts.ingest_docx [--full-rebuild]
"""

import argparse
import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import chromadb
import httpx
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

from app.core.config import settings
from app.core.logging_config import logger
from app.ingestion.discover import discover_documents
from app.ingestion.parsers import parse_docx, parse_xlsx, parse_pdf
from app.ingestion.chunker import create_structure_aware_chunks
from app.ingestion.metadata import compute_file_hash, enrich_chunk_metadata
from app.ingestion.store import persist_chunks_incrementally

load_dotenv(find_dotenv())

# Base folder containing subfolders for different automations
BASE_DOCUMENTS_FOLDER = os.getenv(
    "BASE_DOCUMENTS_FOLDER",
    r"C:\Users\P128F5F\OneDrive - Ceridian HCM Inc\Desktop\AutomationFiles"
)


def get_ai_client():
    """Initializes and returns the OpenAI SDK client instance."""
    if settings.EMBEDDING_MODEL == "nomic-embed-text" or settings.USE_LOCAL_AI:
        return OpenAI(
            base_url=settings.OLLAMA_BASE_URL,
            api_key="ollama",
        )
    else:
        http_client = httpx.Client(verify=False)
        return OpenAI(api_key=settings.OPENAI_API_KEY, http_client=http_client)


def run_ingestion(full_rebuild: bool = False):
    """Main ingestion orchestration workflow."""
    logger.info("Starting Document Ingestion Pipeline...")
    logger.info(f"Target Documents Directory: '{BASE_DOCUMENTS_FOLDER}'")

    discovered_files = discover_documents(BASE_DOCUMENTS_FOLDER)
    if not discovered_files:
        logger.warning("No supported (.docx, .xlsx, .pdf) files found. Ingestion aborted.")
        return

    openai_client = get_ai_client()
    chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)

    all_chunk_payloads = []

    for filepath, file_type, automation in discovered_files:
        filename = os.path.basename(filepath)
        logger.info(f"Processing '{filename}' ({file_type.upper()}) under automation workspace '{automation}'...")

        try:
            # 1. Parse Document into structured elements
            if file_type == "pdf":
                elements = parse_pdf(filepath)
            elif file_type == "xlsx":
                elements = parse_xlsx(filepath)
            else:
                elements = parse_docx(filepath)

            if not elements:
                logger.warning(f"No extractable text found in '{filename}', skipping.")
                continue

            # 2. Compute File SHA-256 Hash
            file_hash = compute_file_hash(filepath)

            # 3. Create Structure-Aware Chunks
            chunks = create_structure_aware_chunks(
                elements,
                target_size=settings.CHUNK_TARGET_SIZE,
                overlap=settings.CHUNK_OVERLAP
            )

            # 4. Enrich Metadata
            for idx, chunk in enumerate(chunks):
                metadata = enrich_chunk_metadata(
                    chunk=chunk,
                    filepath=filepath,
                    file_type=file_type,
                    automation=automation,
                    chunk_index=idx,
                    file_hash=file_hash
                )

                chunk_id = f"{automation}_{filename}_chunk_{idx}"
                all_chunk_payloads.append({
                    "id": chunk_id,
                    "text": chunk["text"],
                    "metadata": metadata
                })

        except Exception as err:
            logger.error(f"Failed to process file '{filename}': {err}")

    # 5. Persist Chunks to ChromaDB
    persist_chunks_incrementally(
        chroma_client=chroma_client,
        collection_name=settings.CHROMA_COLLECTION_NAME,
        all_chunk_payloads=all_chunk_payloads,
        openai_client=openai_client,
        embedding_model=settings.EMBEDDING_MODEL,
        full_rebuild=full_rebuild
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into ChromaDB.")
    parser.add_argument(
        "--full-rebuild",
        action="store_true",
        help="Perform a complete wipe and rebuild of the ChromaDB collection."
    )
    args = parser.parse_args()
    run_ingestion(full_rebuild=args.full_rebuild)
