from google import genai
from google.genai.types import EmbedContentConfig

def embed_query(question: str) -> list[float]:
    client = genai.Client(vertexai=True, project="budgetsense-gcp-prod", location="us-central1")
    result = client.models.embed_content(
        model="text-embedding-005",
        contents=question,
        config=EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=768),
    )
    return result.embeddings[0].values

def vector_search(conn, query_embedding: list[float], top_k: int = 10):
    sql = """
        SELECT id, section_id, chunk_text, source_document, page_number, authority_tier,
               embedding <=> %s::vector AS distance
        FROM document_chunks
        ORDER BY distance
        LIMIT %s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (query_embedding, top_k))
        return cur.fetchall()