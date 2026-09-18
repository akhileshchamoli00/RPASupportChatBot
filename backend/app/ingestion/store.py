"""
ChromaDB storage module with embedding dimension validation and incremental hash-based indexing.
"""

from app.core.logging_config import logger


from app.core.config import settings


def generate_embedding(openai_client, text: str, model_name: str) -> list[float]:
    """Generates an embedding vector for a given text."""
    response = openai_client.embeddings.create(input=text, model=model_name)
    return response.data[0].embedding


def validate_and_get_collection(chroma_client, collection_name: str, test_dim: int):
    """
    Validates collection vector dimension consistency before modifying.
    If dimension mismatch is detected, deletes and re-creates the collection.
    """
    try:
        collection = chroma_client.get_collection(name=collection_name)
        # Inspect existing embeddings if any exist
        existing = collection.get(limit=1, include=["embeddings"])
        if existing and existing.get("embeddings") and len(existing["embeddings"]) > 0:
            existing_dim = len(existing["embeddings"][0])
            if existing_dim != test_dim:
                logger.warning(
                    f"Vector dimension mismatch detected in collection '{collection_name}': "
                    f"Existing={existing_dim}, New={test_dim}. Re-creating collection..."
                )
                chroma_client.delete_collection(name=collection_name)
                collection = chroma_client.create_collection(name=collection_name)
        return collection
    except Exception:
        logger.info(f"Creating new Chroma collection '{collection_name}'...")
        return chroma_client.get_or_create_collection(name=collection_name)


def persist_chunks_incrementally(
    chroma_client,
    collection_name: str,
    all_chunk_payloads: list[dict],
    openai_client,
    embedding_model: str,
    full_rebuild: bool = False
):
    """
    Persists document chunks to ChromaDB with embedding dimension validation and incremental hash indexing.
    """
    if not all_chunk_payloads:
        logger.warning("No chunks provided for persistence.")
        return

    # Test single embedding to determine current model vector dimension
    sample_text = all_chunk_payloads[0]["text"]
    sample_emb = generate_embedding(openai_client, sample_text, embedding_model)
    embedding_dim = len(sample_emb)
    logger.info(f"Active embedding model: '{embedding_model}' | Dimension: {embedding_dim}")

    if full_rebuild:
        logger.info(f"Full rebuild requested. Resetting collection '{collection_name}'...")
        try:
            chroma_client.delete_collection(name=collection_name)
        except Exception:
            pass
        collection = chroma_client.get_or_create_collection(name=collection_name)
    else:
        collection = validate_and_get_collection(chroma_client, collection_name, embedding_dim)

    # Gather existing file hashes from metadata in ChromaDB
    existing_hashes_by_source = {}
    if not full_rebuild and collection.count() > 0:
        existing_data = collection.get(include=["metadatas"])
        for meta in existing_data.get("metadatas", []):
            if meta and "source" in meta and "document_hash" in meta:
                existing_hashes_by_source[meta["source"]] = meta["document_hash"]

    # Filter chunks based on incremental hash analysis
    chunks_to_upsert = []
    sources_to_delete = set()
    skipped_files = set()
    updated_files = set()
    new_files = set()

    for chunk in all_chunk_payloads:
        source = chunk["metadata"]["source"]
        doc_hash = chunk["metadata"]["document_hash"]

        if source in existing_hashes_by_source:
            if existing_hashes_by_source[source] == doc_hash:
                skipped_files.add(source)
                continue
            else:
                updated_files.add(source)
                sources_to_delete.add(source)
                chunks_to_upsert.append(chunk)
        else:
            new_files.add(source)
            chunks_to_upsert.append(chunk)

    # Delete outdated chunks for updated files
    for source in sources_to_delete:
        logger.info(f"Removing outdated chunks for modified file: '{source}'")
        try:
            collection.delete(where={"source": source})
        except Exception as err:
            logger.error(f"Error removing chunks for '{source}': {err}")

    logger.info(
        f"Incremental Ingestion Summary: "
        f"New files={len(new_files)}, Updated={len(updated_files)}, Unchanged/Skipped={len(skipped_files)}"
    )

    if not chunks_to_upsert:
        logger.info("All documents are up-to-date. No new embeddings generated.")
        return

    logger.info(f"Embedding and upserting {len(chunks_to_upsert)} chunks...")

    # Process in batches of 20
    batch_size = 20
    for i in range(0, len(chunks_to_upsert), batch_size):
        batch = chunks_to_upsert[i : i + batch_size]
        ids = [c["id"] for c in batch]
        texts = [c["text"] for c in batch]
        metadatas = [c["metadata"] for c in batch]

        embeddings = []
        for text in texts:
            emb = generate_embedding(openai_client, text, embedding_model)
            embeddings.append(emb)

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

    logger.info(f"Persist Complete! Collection '{collection_name}' now contains {collection.count()} chunks.")
