"""
RAG service — handles embedding, ChromaDB vector + BM25 hybrid retrieval,
distance thresholding, context formatting, and LLM response generation.
"""

import time
from pathlib import Path
import chromadb
import httpx
from openai import OpenAI

from app.core.config import settings
from app.core.logging_config import logger
from app.core.prompts import SYSTEM_PROMPT
from app.core.pii import PIISanitizer

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False
    BM25Okapi = None

try:
    from flashrank import Ranker, RerankRequest
    flashrank_model_path = Path(__file__).resolve().parent.parent.parent / "models" / "flashrank"
    ranker = Ranker(model_name="ms-marco-TinyBERT-L-2-v2", cache_dir=str(flashrank_model_path))
    HAS_FLASHRANK = True
    logger.info("FlashRank neural re-ranker (ms-marco-TinyBERT-L-2-v2) initialized successfully.")
except Exception as err:
    logger.warning(f"FlashRank neural re-ranker could not be initialized: {err}. BM25 fallback will be used.")
    ranker = None
    HAS_FLASHRANK = False

REWRITE_SYSTEM_PROMPT = """You are an AI assistant helping a search retrieval system.
Given a chat history between a user and an RPA Support assistant, and the user's latest follow-up question, rewrite the latest question into a clear, standalone search query that includes any necessary context (such as process names, server names, job names, or error codes) mentioned earlier.

Rules:
- DO NOT answer the question.
- DO NOT add extra commentary or explanations.
- Output ONLY the rewritten search query.
- If the question is already clear and standalone, return it unchanged.
- Keep the query concise and focused on keywords relevant for document retrieval.
- DO NOT append unnecessary generic phrases like "is RPA using" or "in automation" unless specifically required to disambiguate.
"""

# Initialize AI clients (both local Ollama and OpenAI cloud client)
local_client = OpenAI(
    base_url=settings.OLLAMA_BASE_URL,
    api_key="ollama",
)

try:
    http_client = httpx.Client(verify=False)
    cloud_client = OpenAI(api_key=settings.OPENAI_API_KEY, http_client=http_client)
except Exception:
    cloud_client = None

try:
    groq_http_client = httpx.Client(verify=False, timeout=30.0)
    groq_client = OpenAI(
        base_url=settings.GROQ_BASE_URL,
        api_key=settings.GROQ_API_KEY or "none",
        http_client=groq_http_client
    ) if settings.GROQ_API_KEY else None
except Exception as err:
    logger.warning(f"Failed to initialize Groq client: {err}")
    groq_client = None

# Default client reference
openai_client = local_client if settings.USE_LOCAL_AI else cloud_client

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)


def _get_collection():
    """Get the ChromaDB collection (lazy so it doesn't fail at import time)."""
    return chroma_client.get_collection(name=settings.CHROMA_COLLECTION_NAME)


import time


def generate_embedding(text: str) -> list[float]:
    """Convert text into an embedding vector using the configured embedding model."""
    model_name = settings.EMBEDDING_MODEL

    if model_name == "nomic-embed-text":
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = local_client.embeddings.create(
                    input=text,
                    model=model_name,
                )
                return response.data[0].embedding
            except Exception as err:
                if attempt < max_retries - 1:
                    logger.warning(f"Ollama embedding attempt {attempt+1} failed ({err}). Retrying in 1s...")
                    time.sleep(1)
                else:
                    logger.error(f"Failed to generate embedding via Ollama after {max_retries} attempts: {err}")
                    raise RuntimeError("Ollama local embedding service is offline or restarting. Please ensure Ollama is running.")
    else:
        if not cloud_client or not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required for cloud embeddings.")
        response = cloud_client.embeddings.create(
            input=text,
            model=model_name,
        )
        return response.data[0].embedding




STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few", "for",
    "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's",
    "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm",
    "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't",
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't",
    "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't",
    "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's",
    "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves"
}


def _tokenize_text(text: str) -> list[str]:
    words = text.lower().replace('/', ' ').replace(':', ' ').replace('-', ' ').split()
    return [w.strip(".,()[]{}") for w in words if w.strip(".,()[]{}") not in STOP_WORDS and len(w.strip(".,()[]{}")) > 1]


def _apply_bm25_rescoring(query: str, candidates: list[dict]) -> list[dict]:
    """Helper to apply BM25 / lexical keyword rescoring as fallback."""
    query_tokens = _tokenize_text(query)
    if not query_tokens or len(candidates) <= 1:
        return candidates

    if HAS_BM25 and BM25Okapi is not None:
        tokenized_corpus = [_tokenize_text(c["text"]) for c in candidates]
        bm25 = BM25Okapi(tokenized_corpus)
        bm25_scores = list(bm25.get_scores(query_tokens))
        # If BM25 IDF zeroed out (e.g. tiny candidate set where log(1.5/1.5)=0), fallback to lexical count
        if max(bm25_scores) <= 0.0:
            bm25_scores = []
            for c in candidates:
                words = set(_tokenize_text(c["text"]))
                matches = sum(1 for w in query_tokens if w in words)
                bm25_scores.append(float(matches))
    else:
        # Fallback simple lexical term frequency matching
        bm25_scores = []
        for c in candidates:
            words = set(_tokenize_text(c["text"]))
            matches = sum(1 for w in query_tokens if w in words)
            bm25_scores.append(float(matches))

    max_score = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
    for idx, candidate in enumerate(candidates):
        norm_lexical = bm25_scores[idx] / max_score
        vec_score = 1.0 / (1.0 + candidate["distance"])
        # Combined score: 70% dense vector similarity + 30% lexical keyword match
        candidate["hybrid_score"] = (0.7 * vec_score) + (0.3 * norm_lexical)

    candidates.sort(key=lambda x: x.get("hybrid_score", 0.0), reverse=True)
    return candidates


def retrieve_relevant_documents(
    query: str,
    top_k: int = None,
    automation: str = None
) -> tuple[list[str], list[dict]]:
    """
    Retrieves documents using dense vector search + FlashRank neural re-ranking
    (with BM25 hybrid fallback), applying similarity distance thresholding.

    Returns a tuple: (retrieved_text_chunks, source_citation_metadatas).
    """
    k = top_k or settings.TOP_K
    logger.info(f"RAG Retrieval initiated for query: '{query[:60]}...' | Workspace: '{automation}'")

    # Step 1: Embed query vector
    query_embedding = generate_embedding(query)
    collection = _get_collection()

    # Query dense candidates (fetch top candidates for re-ranking)
    candidate_limit = max(k * 3, 10)
    query_args = {
        "query_embeddings": [query_embedding],
        "n_results": candidate_limit,
        "include": ["documents", "metadatas", "distances"]
    }
    if automation and automation.strip().lower() not in ("general", "all"):
        query_args["where"] = {"automation": automation}

    try:
        results = collection.query(**query_args)
    except Exception as err:
        logger.error(f"ChromaDB query error: {err}")
        return [], []

    raw_docs = results.get("documents", [[]])[0]
    raw_metas = results.get("metadatas", [[]])[0]
    raw_dists = results.get("distances", [[]])[0]

    if not raw_docs:
        logger.info("No candidates returned from vector database.")
        return [], []

    # Step 2: Distance Thresholding
    threshold = settings.SIMILARITY_THRESHOLD
    valid_candidates = []
    for doc, meta, dist in zip(raw_docs, raw_metas, raw_dists):
        # Chroma L2 distance: lower is closer. Check distance threshold.
        if dist <= threshold:
            valid_candidates.append({
                "id": len(valid_candidates),
                "text": doc,
                "metadata": meta,
                "distance": dist
            })
        else:
            logger.debug(f"Candidate chunk distance ({dist:.3f}) exceeded threshold ({threshold}).")

    if not valid_candidates:
        logger.info("All retrieved candidate chunks exceeded similarity distance threshold.")
        return [], []

    # Step 3: Neural Re-ranking with FlashRank + RRF (BM25 Hybrid Fallback)
    if HAS_FLASHRANK and ranker is not None and len(valid_candidates) > 1:
        try:
            passages = [{"id": c["id"], "text": c["text"]} for c in valid_candidates]
            rerank_req = RerankRequest(query=query, passages=passages)
            ranked_results = ranker.rerank(rerank_req)

            # Reciprocal Rank Fusion (RRF): fuses dense vector similarity rank with FlashRank neural rank.
            # This prevents near-zero cross-encoder scores from accidentally suppressing the top dense semantic match.
            rrf_scores = {}
            for vec_rank, c in enumerate(valid_candidates):
                rrf_scores[c["id"]] = 1.0 / (60.0 + vec_rank + 1)
            for fr_rank, r in enumerate(ranked_results):
                rrf_scores[r["id"]] += 1.0 / (60.0 + fr_rank + 1)

            for r in ranked_results:
                for c in valid_candidates:
                    if c["id"] == r["id"]:
                        c["rank_score"] = r.get("score", 0.0)
                        c["rrf_score"] = rrf_scores[c["id"]]

            valid_candidates.sort(key=lambda x: rrf_scores[x["id"]], reverse=True)
            logger.info(f"FlashRank neural re-ranking with RRF applied to {len(valid_candidates)} candidates.")
        except Exception as fr_err:
            logger.warning(f"FlashRank neural re-ranking failed ({fr_err}). Falling back to BM25.")
            if settings.ENABLE_HYBRID_SEARCH:
                valid_candidates = _apply_bm25_rescoring(query, valid_candidates)
    elif settings.ENABLE_HYBRID_SEARCH and len(valid_candidates) > 1:
        valid_candidates = _apply_bm25_rescoring(query, valid_candidates)


    # Select Top-K final candidates
    selected = valid_candidates[:k]
    selected_texts = [item["text"] for item in selected]
    selected_metas = [item["metadata"] for item in selected]

    logger.info(f"Retrieval complete. Retained {len(selected)} chunks passing similarity thresholding.")

    # Print Top-K raw chunks as-is after re-ranking directly to the terminal
    print("\n" + "=" * 80, flush=True)
    print(f" >>> [TOP-{len(selected)} RE-RANKED CHUNKS - RAW DATA] (Query: '{query}')", flush=True)
    print("=" * 80, flush=True)
    for rank, item in enumerate(selected, 1):
        meta = item.get("metadata", {})
        fname = meta.get("file_name", "Unknown")
        sec = meta.get("section", "N/A")
        ws = meta.get("workspace", "N/A")
        dist = item.get("distance", 0.0)
        score_parts = [f"Vector L2 Dist: {dist:.4f}"]
        if "rank_score" in item:
            score_parts.append(f"FlashRank Neural Score: {item['rank_score']:.4f}")
        elif "hybrid_score" in item:
            score_parts.append(f"BM25 Hybrid Score: {item['hybrid_score']:.4f}")
        score_info = " | ".join(score_parts)

        print(f"\n--- [Rank {rank}/{len(selected)}] {fname} | Workspace: {ws} ---", flush=True)
        print(f"Section: {sec} | {score_info}", flush=True)
        print("-" * 60, flush=True)
        print(item.get("text", "").strip(), flush=True)
    print("=" * 80 + "\n", flush=True)

    return selected_texts, selected_metas



def rewrite_query_with_context(
    query: str,
    conversation_history: list[dict],
    target_client=None,
    model: str = None
) -> str:
    """
    Rewrites a follow-up query to include conversational context for vector search.
    Resolves pronouns ('it', 'that', 'its') and ambiguous follow-ups into standalone search queries.
    If history is empty or LLM rewrite fails, returns the original query.
    """
    if not conversation_history:
        return query

    # Filter out empty or UI control messages
    recent_history = [
        m for m in conversation_history[-4:]
        if m.get("content") and not str(m.get("content")).startswith("[AUTOMATION_")
    ]
    if not recent_history:
        return query

    history_text = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in recent_history])
    if not history_text.strip():
        return query

    client = target_client or groq_client or local_client
    chosen_model = model or (settings.GROQ_MODEL if client == groq_client else settings.CHAT_MODEL)

    prompt = f"Chat History:\n{history_text}\n\nLatest Question:\n{query}\n\nStandalone Query:"
    try:
        res = client.chat.completions.create(
            model=chosen_model,
            messages=[
                {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=60
        )
        rewritten = res.choices[0].message.content.strip().strip('"').strip("'")
        # Ensure single line response without hallucinated answers
        if rewritten and len(rewritten) > 2 and "\n" not in rewritten:
            logger.info(f"Context-aware query rewritten: '{query}' -> '{rewritten}'")
            return rewritten
    except Exception as err:
        logger.warning(f"Query rewriting failed ({err}). Proceeding with original query.")

    return query


def build_context_prompt(retrieved_docs: list[str], metadatas: list[dict]) -> str:
    """Format retrieved documents and source citations into a context block for the LLM."""
    if not retrieved_docs:
        return "No relevant context was found in the knowledge base."

    context_parts = []
    for i, (doc, meta) in enumerate(zip(retrieved_docs, metadatas), 1):
        source = meta.get("source", "Unknown Document")
        page = meta.get("page", 0)
        sheet = meta.get("sheet", "")
        row_start = meta.get("row_start", 0)
        row_end = meta.get("row_end", 0)
        section = meta.get("section", "General")
        automation = meta.get("automation", "General")

        header_details = [f"File: {source}"]
        if page and page > 0:
            header_details.append(f"Page: {page}")
        if sheet:
            header_details.append(f"Sheet: {sheet}")
        if row_start and row_start > 0:
            header_details.append(f"Rows: {row_start}-{row_end}")
        header_details.append(f"Section: {section}")
        header_details.append(f"Workspace: {automation}")

        header_str = " | ".join(header_details)
        context_parts.append(f"--- Source {i} ---\n{header_str}\n{doc}")

    return "\n\n".join(context_parts)


def generate_chat_response(
    user_query: str,
    conversation_history: list[dict],
    automation: str = None,
    use_local_ai: bool = None,
    ai_provider: str = None,
) -> dict:
    """
    Full RAG pipeline:
    1. Resolve AI provider & client
    2. Context-aware query rewriting for ambiguous follow-up questions
    3. Retrieve relevant documents from ChromaDB with distance thresholding & FlashRank neural re-ranking
    4. Format prompt context with source citations
    5. Generate LLM chat completion using Groq, Local Ollama, or OpenAI ChatGPT
    6. Return dictionary: {"response": str, "sources": list[dict], "token_usage": dict}
    """
    # Step 1 — Resolve AI provider and client
    global groq_client
    provider = "groq"
    if ai_provider:
        provider = ai_provider.lower()
    elif use_local_ai is not None:
        provider = "local" if use_local_ai else "chatgpt"
    else:
        provider = getattr(settings, "AI_PROVIDER", "local").lower()

    if provider == "groq":
        if groq_client is None and settings.GROQ_API_KEY:
            try:
                groq_client = OpenAI(
                    base_url=settings.GROQ_BASE_URL,
                    api_key=settings.GROQ_API_KEY,
                    http_client=httpx.Client(verify=False, timeout=30.0)
                )
            except Exception as e:
                logger.error(f"Error re-initializing Groq client: {e}")

        if not groq_client or not settings.GROQ_API_KEY:
            logger.warning("Groq AI requested but GROQ_API_KEY is not set. Falling back to Local AI...")
            target_client = local_client
            chat_model = settings.CHAT_MODEL
        else:
            target_client = groq_client
            chat_model = settings.GROQ_MODEL
            logger.info(f"Generating LLM response using Groq LPU ({chat_model})...")

    elif provider == "local":
        target_client = local_client
        chat_model = settings.CHAT_MODEL
        logger.info(f"Generating LLM response using Local AI ({chat_model})...")

    else:
        if not cloud_client or not settings.OPENAI_API_KEY:
            logger.warning("Cloud AI requested but OPENAI_API_KEY is not set. Falling back to Local AI...")
            target_client = local_client
            chat_model = settings.CHAT_MODEL
        else:
            target_client = cloud_client
            chat_model = "gpt-4o-mini"
            logger.info(f"Generating LLM response using Cloud ChatGPT ({chat_model})...")

    # Step 2 — Context-Aware Query Rewriting (resolve follow-up pronouns)
    effective_query = rewrite_query_with_context(
        query=user_query,
        conversation_history=conversation_history,
        target_client=target_client,
        model=chat_model
    )

    # Step 3 — Retrieve
    retrieved_docs, retrieved_metas = retrieve_relevant_documents(effective_query, automation=automation)

    # Check for controlled insufficient evidence response
    if not retrieved_docs:
        insufficient_msg = "I couldn't find relevant information in the knowledge base."
        return {
            "response": insufficient_msg,
            "sources": [],
            "token_usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "model": "none",
            },
        }

    # Step 4 — Build context with citations (cap size to ensure we stay well within token budgets)
    context_block = build_context_prompt(retrieved_docs, retrieved_metas)
    if len(context_block) > 8000:
        context_block = context_block[:8000] + "\n...[Context truncated to fit model token limit]"

    # Print retrieved chunks BEFORE masking to terminal
    print("\n" + "=" * 80, flush=True)
    print(" >>> [RETRIEVED CHUNKS - BEFORE MASKING]", flush=True)
    print("=" * 80, flush=True)
    for idx, (doc, meta) in enumerate(zip(retrieved_docs, retrieved_metas), 1):
        fname = meta.get("file_name", "Unknown")
        sec = meta.get("section", "N/A")
        ws = meta.get("workspace", "N/A")
        print(f"\n--- Chunk {idx} [{fname} | Workspace: {ws} | Section: {sec}] ---", flush=True)
        print(doc.strip(), flush=True)
    print("-" * 80, flush=True)

    # PII Masking: Reversible Pseudonymization for Cloud LLMs (Groq / ChatGPT)
    # When using local models (Ollama), data never leaves localhost so masking is bypassed for zero overhead.
    is_cloud_provider = (provider in ["groq", "chatgpt"])
    sanitizer = PIISanitizer() if is_cloud_provider else None

    if sanitizer:
        # Mask the full context block and query
        context_block = sanitizer.mask(context_block)
        user_query_for_llm = sanitizer.mask(user_query)
        if sanitizer.has_pii:
            logger.info(f"Reversibly pseudonymized {sanitizer.count} PII items before cloud dispatch ({provider}).")

        # Print retrieved chunks AFTER masking to terminal
        print("\n" + "=" * 80, flush=True)
        print(f" >>> [RETRIEVED CHUNKS - AFTER MASKING (Provider: {provider})]", flush=True)
        print("=" * 80, flush=True)
        if sanitizer.has_pii:
            print(f"Masked Entities Vault ({sanitizer.count} items replaced):", flush=True)
            for raw_val, tok in sanitizer.forward_vault.items():
                print(f"  * {tok} <-- {raw_val}", flush=True)

            print("\nMasked Chunks with Protected Tokens:", flush=True)
            for idx, (doc, meta) in enumerate(zip(retrieved_docs, retrieved_metas), 1):
                fname = meta.get("file_name", "Unknown")
                sec = meta.get("section", "N/A")
                ws = meta.get("workspace", "N/A")
                masked_chunk = sanitizer.mask(doc.strip())
                print(f"\n--- Masked Chunk {idx} [{fname} | Workspace: {ws} | Section: {sec}] ---", flush=True)
                print(masked_chunk, flush=True)
        else:
            print("No PII entities detected in retrieved context.", flush=True)
        print("=" * 80 + "\n", flush=True)
    else:
        print("\n" + "=" * 80, flush=True)
        print(f" >>> [LOCAL MODEL: MASKING BYPASSED (Provider: {provider} on localhost)]", flush=True)
        print(" Raw chunks sent directly to local Ollama model without modification.", flush=True)
        print("=" * 80 + "\n", flush=True)
        user_query_for_llm = user_query



    # Step 5 — Assemble messages
    context_instruction = (
        "Below is the relevant context retrieved from the knowledge base. "
        "Use ONLY this context to answer the user's question.\n"
    )
    if sanitizer and sanitizer.has_pii:
        context_instruction += (
            "IMPORTANT: If the context contains placeholder tokens like __EMAIL_1__ or __SVC_ACCOUNT_1__, "
            "retain them EXACTLY as written in your response so they can be securely resolved.\n"
        )
    context_instruction += f"\n{context_block}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": context_instruction,
        },
    ]

    # Append prior conversation history (sliding window: retain last 4 messages to preserve context without exceeding rate limits)
    trimmed_history = conversation_history[-4:] if len(conversation_history) > 4 else conversation_history
    if sanitizer:
        sanitized_history = []
        for m in trimmed_history:
            content = m.get("content", "")
            sanitized_history.append({
                **m,
                "content": sanitizer.mask(content) if isinstance(content, str) else content
            })
        messages.extend(sanitized_history)
    else:
        messages.extend(trimmed_history)

    # Append current user query
    messages.append({"role": "user", "content": user_query_for_llm})

    # Step 6 — LLM Generation
    create_kwargs = {
        "model": chat_model,
        "messages": messages,
        "temperature": 0,
    }

    if provider == "local":
        create_kwargs["extra_body"] = {
            "options": {
                "num_ctx": 2048,     # Limit context window to speed up CPU prompt evaluation
                "num_predict": 512,  # Limit max output tokens
            },
            "keep_alive": "1h"       # Keep model warm in RAM for instant subsequent requests
        }

    try:
        response = target_client.chat.completions.create(**create_kwargs)
    except Exception as api_err:
        # If Groq fails due to model access or rate limits, fallback gracefully
        if provider == "groq" and local_client:
            logger.warning(f"Groq generation failed ({api_err}). Falling back to Local AI...")
            create_kwargs["model"] = settings.CHAT_MODEL
            response = local_client.chat.completions.create(**create_kwargs)
        else:
            raise api_err

    reply_text = response.choices[0].message.content

    # Step 6.1 — Restore PII if cloud pseudonymization was active
    if sanitizer and sanitizer.has_pii and reply_text:
        reply_text = sanitizer.restore(reply_text)


    # Extract token usage metrics across all models (Ollama, Groq, ChatGPT)
    actual_model = getattr(response, "model", None) or create_kwargs.get("model", "unknown")
    usage_data = getattr(response, "usage", None)

    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0

    if usage_data:
        if isinstance(usage_data, dict):
            prompt_tokens = usage_data.get("prompt_tokens", 0)
            completion_tokens = usage_data.get("completion_tokens", 0)
            total_tokens = usage_data.get("total_tokens", 0)
        else:
            prompt_tokens = getattr(usage_data, "prompt_tokens", 0) or 0
            completion_tokens = getattr(usage_data, "completion_tokens", 0) or 0
            total_tokens = getattr(usage_data, "total_tokens", 0) or 0

    # If usage is not reported by a local backend or mock, calculate robust token estimate
    if total_tokens == 0:
        prompt_chars = sum(len(m.get("content", "")) for m in messages)
        completion_chars = len(reply_text) if reply_text else 0
        prompt_tokens = max(1, prompt_chars // 4)
        completion_tokens = max(1, completion_chars // 4)
        total_tokens = prompt_tokens + completion_tokens

    token_usage = {
        "prompt_tokens": int(prompt_tokens),
        "completion_tokens": int(completion_tokens),
        "total_tokens": int(total_tokens),
        "model": actual_model,
    }

    # Prepare citation list for API response metadata including raw snippet excerpt
    unique_sources = []
    seen_sources = set()
    for doc, meta in zip(retrieved_docs, retrieved_metas):
        src_key = (meta.get("source"), meta.get("page"), meta.get("sheet"), meta.get("section"))
        if src_key not in seen_sources:
            seen_sources.add(src_key)
            unique_sources.append({
                "source": meta.get("source"),
                "file_type": meta.get("file_type"),
                "automation": meta.get("automation"),
                "page": meta.get("page"),
                "sheet": meta.get("sheet"),
                "section": meta.get("section"),
                "row_start": meta.get("row_start"),
                "row_end": meta.get("row_end"),
                "snippet": doc.strip() if doc else "",
            })

    return {
        "response": reply_text,
        "sources": unique_sources,
        "token_usage": token_usage,
    }

