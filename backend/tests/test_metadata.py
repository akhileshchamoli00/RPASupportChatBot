"""
Unit tests for metadata enrichment and SHA-256 file hashing.
"""

from app.ingestion.metadata import compute_file_hash, enrich_chunk_metadata


def test_compute_file_hash(tmp_path):
    """Verifies SHA-256 calculation on file binary content."""
    filepath = str(tmp_path / "test.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("Test content for hashing")

    hash1 = compute_file_hash(filepath)
    assert len(hash1) == 64  # SHA-256 hex string length

    # Modifying content changes hash
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("Modified content")

    hash2 = compute_file_hash(filepath)
    assert hash1 != hash2


def test_enrich_chunk_metadata():
    """Verifies metadata dict construction with primitive types for ChromaDB."""
    chunk = {
        "text": "Sample chunk text",
        "page": 3,
        "sheet": "Errors",
        "row_start": 10,
        "row_end": 12,
        "section": "Troubleshooting",
        "title": "ROE_Manual.pdf"
    }

    meta = enrich_chunk_metadata(
        chunk=chunk,
        filepath="/path/to/ROE_Manual.pdf",
        file_type="pdf",
        automation="ROE",
        chunk_index=2,
        file_hash="dummyhash123"
    )

    assert meta["source"] == "ROE_Manual.pdf"
    assert meta["file_type"] == "pdf"
    assert meta["automation"] == "ROE"
    assert meta["chunk_index"] == 2
    assert meta["page"] == 3
    assert meta["sheet"] == "Errors"
    assert meta["document_hash"] == "dummyhash123"
