"""
Unit tests for retrieval context prompt formatting and citation metadata handling.
"""

from app.services.rag_service import build_context_prompt


def test_build_context_prompt_formatting():
    """Verifies context prompt formatting includes structured source citation headers."""
    retrieved_docs = [
        "First document text snippet describing ROE credentials.",
        "Second document text snippet detailing error 401 resolution."
    ]
    metadatas = [
        {
            "source": "ROE_Guide.pdf",
            "page": 3,
            "sheet": "",
            "row_start": 0,
            "row_end": 0,
            "section": "Credential Setup",
            "automation": "ROE"
        },
        {
            "source": "SupportMatrix.xlsx",
            "page": 0,
            "sheet": "ErrorCodes",
            "row_start": 10,
            "row_end": 12,
            "section": "Sheet: ErrorCodes",
            "automation": "General"
        }
    ]

    context_str = build_context_prompt(retrieved_docs, metadatas)
    assert "--- Source 1 ---" in context_str
    assert "File: ROE_Guide.pdf | Page: 3" in context_str
    assert "Workspace: ROE" in context_str
    assert "--- Source 2 ---" in context_str
    assert "File: SupportMatrix.xlsx | Sheet: ErrorCodes | Rows: 10-12" in context_str


def test_rewrite_query_with_context_empty_history():
    """Verifies that an empty conversation history returns the original user query untouched."""
    from app.services.rag_service import rewrite_query_with_context
    original = "Where is the ROE configuration file?"
    assert rewrite_query_with_context(original, []) == original


def test_rewrite_query_with_context_mock_client():
    """Verifies that rewrite_query_with_context formats prompt and parses LLM rewrite."""
    from unittest.mock import MagicMock
    from app.services.rag_service import rewrite_query_with_context

    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "ROE configuration file path"
    mock_client.chat.completions.create.return_value.choices = [mock_choice]

    history = [
        {"role": "user", "content": "How do I setup ROE?"},
        {"role": "assistant", "content": "You need to edit the configuration file first."}
    ]
    query = "Where is it located?"

    rewritten = rewrite_query_with_context(query, history, target_client=mock_client, model="test-model")
    assert rewritten == "ROE configuration file path"
    assert mock_client.chat.completions.create.called


def test_bm25_rescoring_fallback():
    """Verifies BM25 rescoring reorders candidates based on lexical token matches."""
    from app.services.rag_service import _apply_bm25_rescoring

    candidates = [
        {"text": "General system setup with network protocols.", "distance": 0.2},
        {"text": "ROE error code 401 unauthorized access resolution.", "distance": 0.3},
    ]
    rescored = _apply_bm25_rescoring("ROE 401 error", candidates)
    # The second candidate has strong lexical overlap with "ROE 401 error"
    assert rescored[0]["text"].startswith("ROE error code 401")

