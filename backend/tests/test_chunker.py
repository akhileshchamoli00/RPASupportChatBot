"""
Unit tests for structure-aware text chunking.
"""

from app.ingestion.chunker import create_structure_aware_chunks


def test_structure_aware_chunking_grouping():
    """Verifies chunker groups elements up to target_size without breaking sequence."""
    elements = [
        {"text": "Paragraph 1: Overview of Dayforce ROE.", "section": "Overview", "title": "Guide.pdf", "page": 1},
        {"text": "Paragraph 2: Prerequisites for configuration.", "section": "Overview", "title": "Guide.pdf", "page": 1},
        {"text": "Step 1: Navigate to Setup menu.", "section": "Steps", "title": "Guide.pdf", "page": 2},
        {"text": "Step 2: Enter credentials.", "section": "Steps", "title": "Guide.pdf", "page": 2},
    ]

    chunks = create_structure_aware_chunks(elements, target_size=1000, overlap=50)
    assert len(chunks) == 1
    assert "Overview of Dayforce ROE" in chunks[0]["text"]
    assert "Step 2: Enter credentials" in chunks[0]["text"]
    assert chunks[0]["page"] == 1


def test_chunker_large_elements():
    """Verifies elements exceeding target size are handled safely."""
    large_text = "A" * 1500
    elements = [
        {"text": large_text, "section": "LargeSection", "title": "Doc.pdf", "page": 1}
    ]

    chunks = create_structure_aware_chunks(elements, target_size=500, overlap=50)
    assert len(chunks) == 1
    assert len(chunks[0]["text"]) == 1500
