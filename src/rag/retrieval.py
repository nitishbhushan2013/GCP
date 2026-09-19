from google import genai
from google.genai.types import EmbedContentConfig
import re


def embed_query(question: str) -> list[float]:
    client = genai.Client(vertexai=True, project="budgetsense-gcp-prod", location="us-central1")
    result = client.models.embed_content(
        model="text-embedding-005",
        contents=question,
        config=EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=768),
    )
    return result.embeddings[0].values

# <=> is pgvector's cosine distance operator — lower is better (0 = identical).
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


"""
plainto_tsquery (not to_tsquery) — it takes plain natural-language text and handles the tokenizing/stemming itself, 
                                    so you can pass the raw question straight in, same as the vector side.
plainto_tsquery's default logic: it ANDs every word together. Your question "What is the WATO tax offset amount?" becomes 'wato' & 'tax' & 'offset' & 'amount'
                                AND requires every term to match, zero rows return, even though three of the four terms are a perfect match.
ts_rank gives a relevance score, higher is better — opposite direction from C1's cosine distance (lower is better). 
WHERE search_vector @@ ... means this can return zero rows if no keyword matches at all 
                    — unlike vector search, which always returns something (even a bad match). That's expected and actually useful: it's the lexical signal saying "no exact term match here."
"""


def build_or_query(conn, question: str) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT to_tsvector('english', %s)::text", (question,))
        tsvector_str = cur.fetchone()[0]
    lexemes = re.findall(r"'([^']+)'", tsvector_str)
    return ' | '.join(lexemes)

def full_text_search(conn, question: str, top_k: int = 10):
    tsquery_str = build_or_query(conn, question)
    sql = """
        SELECT id, section_id, chunk_text, source_document, page_number, authority_tier,
               ts_rank(search_vector, to_tsquery('english', %s)) AS rank
        FROM document_chunks
        WHERE search_vector @@ to_tsquery('english', %s)
        ORDER BY rank DESC
        LIMIT %s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (tsquery_str, tsquery_str, top_k))
        return cur.fetchall()

"""
RRF is meant to produce: a chunk that both search methods independently agree on (even if neither ranks it #1) 
beats a chunk that one method loves but the other never sees. It's rewarding consensus over 
any single method's confidence.

The idea: take each result list, use rank position (1st, 2nd, 3rd...) 
this sidesteps the fact that cosine distance (lower=better) and 
ts_rank (higher=better) aren't on comparable scales. Each chunk's 
final score is the sum of 1/(k+rank) across whichever lists it appears in,
 where k (typically 60) dampens the effect of rank 1 vs rank 2 so it's not overly extreme.

 chunks[chunk_id] = row gets overwritten if a chunk appears in both lists — harmless, since the row data itself is
   identical either way, only the rank (and thus score contribution) differs per list.
A chunk appearing in both lists naturally accumulates a higher combined score than one appearing in only one — \
    that's RRF's core benefit, without us writing any special-case logic for it.
k=60 is the standard default from the original RRF paper — dampens rank-1-vs-rank-2 swings so one search 
method doesn't totally dominate just by narrowly edging out a rank position.

"""
def rrf_fuse(vector_results, fulltext_results, k: int = 60, top_k: int = 10):
    scores = {}
    chunks = {}

    for rank, row in enumerate(vector_results, start=1):
        chunk_id = row[0]
        chunks[chunk_id] = row
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank)

    for rank, row in enumerate(fulltext_results, start=1):
        chunk_id = row[0]
        chunks[chunk_id] = row
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank)

    ranked_ids = sorted(scores, key=scores.get, reverse=True)[:top_k]
    return [(chunks[cid], scores[cid]) for cid in ranked_ids]


"""
Sure — walking through build_or_query step by step, since that's the new/confusing part:

The problem it solves: we need to turn a natural question into a Postgres tsquery (Postgres's search-term format), using the exact same rules Postgres already used when it built search_vector — otherwise the two sides won't line up.

Step 1:

python
cur.execute("SELECT to_tsvector('english', %s)::text", (question,))
tsvector_str = cur.fetchone()[0]

We hand the question itself to Postgres's to_tsvector('english', ...) — the same function that processed every chunk during ingestion. It strips stopwords ("what", "is", "the"), stems words to their root form ("offset" stays "offset", but something like "running" would become "run"), and returns them as a tsvector.

For "What is the WATO tax offset amount?" this returns something like:

'amount':6 'offset':5 'tax':4 'wato':2

That's Postgres's own answer to "these are the meaningful search terms, stemmed and de-stopworded."

Step 2:

python
lexemes = re.findall(r"'([^']+)'", tsvector_str)

That string is text, not a Python list — so this pulls out just the words between quotes (amount, offset, tax, wato), throwing away the position numbers we don't need.

Step 3:

python
return ' | '.join(lexemes)

Joins them with | (OR) into wato | tax | offset | amount — a valid to_tsquery string meaning "match any chunk containing at least one of these terms."
"""