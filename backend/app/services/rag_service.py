"""
RAG service — handles embedding, ChromaDB retrieval, and LLM response generation.
"""

import chromadb
from openai import OpenAI

from app.core.config import settings
from app.core.prompts import SYSTEM_PROMPT


# Initialize OpenAI client
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Initialize ChromaDB client and get the collection
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)


def _get_collection():
    """Get the ChromaDB collection (lazy so it doesn't fail at import time)."""
    return chroma_client.get_collection(name=settings.CHROMA_COLLECTION_NAME)


def generate_embedding(text: str) -> list[float]:
    """Convert text into an embedding vector using OpenAI."""
    response = openai_client.embeddings.create(
        input=text,
        model=settings.EMBEDDING_MODEL,
    )
    return response.data[0].embedding


def retrieve_relevant_documents(query: str, top_k: int = None) -> list[str]:
    """
    Embed the query and perform similarity search on ChromaDB.
    Returns the text content of the top-k most relevant documents.
    """
    k = top_k or settings.TOP_K
    query_embedding = generate_embedding(query)

    collection = _get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
    )

    # results["documents"] is a list of lists — flatten the first (only) query
    documents = results.get("documents", [[]])[0]
    return documents


def build_context_prompt(retrieved_docs: list[str]) -> str:
    """Format retrieved documents into a context block for the LLM."""
    if not retrieved_docs:
        return "No relevant context was found in the knowledge base."

    context_parts = []
    for i, doc in enumerate(retrieved_docs, 1):
        context_parts.append(f"--- Document {i} ---\n{doc}")

    return "\n\n".join(context_parts)


def generate_chat_response(
    user_query: str,
    conversation_history: list[dict],
) -> str:
    """
    Full RAG pipeline:
    1. Retrieve relevant documents from ChromaDB
    2. Build a context-augmented prompt
    3. Send to OpenAI chat model with conversation history
    4. Return the assistant's reply
    """
    # Step 1 — Retrieve
    retrieved_docs = retrieve_relevant_documents(user_query)

    # Step 2 — Build context
    context_block = build_context_prompt(retrieved_docs)
    print("Context Block:", context_block)
    print("Retrieved Documents:", retrieved_docs)
    # Step 3 — Assemble messages
    messages = [    
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                "Below is the relevant context retrieved from the knowledge base. "
                "Use ONLY this context to answer the user's question.\n\n"
                f"{context_block}"
            ),
        },
    ]

    # Append conversation history (prior user/assistant turns)
    messages.extend(conversation_history)

    # Append the current user query
    messages.append({"role": "user", "content": user_query})

    # Step 4 — Generate
    response = openai_client.chat.completions.create(
        model=settings.CHAT_MODEL,
        messages=messages,
        temperature=1,  # Low temperature for factual answers
    )

    return response.choices[0].message.content
