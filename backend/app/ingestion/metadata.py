"""
Metadata enrichment and SHA-256 file hashing module.
"""

import hashlib
import os


from app.ingestion.utils import read_file_bytes_safely


def compute_file_hash(filepath: str) -> str:
    """Computes SHA-256 hash of file contents for incremental indexing."""
    sha256 = hashlib.sha256()
    file_data = read_file_bytes_safely(filepath)
    sha256.update(file_data)
    return sha256.hexdigest()



def enrich_chunk_metadata(
    chunk: dict,
    filepath: str,
    file_type: str,
    automation: str,
    chunk_index: int,
    file_hash: str
) -> dict:
    """
    Constructs a strict, primitive-value metadata dictionary for ChromaDB storage.
    """
    filename = os.path.basename(filepath)
    
    metadata = {
        "source": filename,
        "file_type": file_type,
        "automation": automation,
        "chunk_index": chunk_index,
        "page": chunk.get("page") if chunk.get("page") is not None else 0,
        "sheet": chunk.get("sheet") or "",
        "row_start": chunk.get("row_start") if chunk.get("row_start") is not None else 0,
        "row_end": chunk.get("row_end") if chunk.get("row_end") is not None else 0,
        "section": chunk.get("section") or "General",
        "title": chunk.get("title") or filename,
        "document_hash": file_hash,
    }
    
    return metadata
