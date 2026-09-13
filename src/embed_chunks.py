"""
Epic 6 / Phase B / B6 — Embedding generation via Vertex AI text-embedding-005 (google-genai SDK).
"""

from google import genai
from google.genai import types as genai_types

PROJECT_ID = "budgetsense-gcp-prod"
LOCATION = "australia-southeast1"
EMBEDDING_MODEL = "text-embedding-005"
EXPECTED_DIMENSIONS = 768

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    return _client


def embed_chunks(chunk_texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of child chunks (ingestion path —
    RETRIEVAL_DOCUMENT task type). Returns one 768-dim vector per input
    chunk, same order."""
    client = _get_client()
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=chunk_texts,
        config=genai_types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
    )
    vectors = [e.values for e in response.embeddings]
    for v in vectors:
        assert len(v) == EXPECTED_DIMENSIONS, (
            f"Expected {EXPECTED_DIMENSIONS}-dim embedding, got {len(v)}"
        )
    return vectors


def embed_query(query_text: str) -> list[float]:
    """Generate an embedding for a user's search query (RETRIEVAL_QUERY
    task type). Used later in Phase C."""
    client = _get_client()
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[query_text],
        config=genai_types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return response.embeddings[0].values