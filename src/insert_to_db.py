"""
Epic 6 / Phase B / B7 — Insert parent sections and child chunks into Cloud SQL.
"""

import os
import psycopg

#from parse_pdfs_batch import batch_process_pdfs
from parse_pdfs_batch import load_existing_batch_output
from test_parent_sections import extract_page_texts, build_parent_sections
from split_child_chunks import split_into_child_chunks
from embed_chunks import embed_chunks
from authority_tiers import get_authority_tier
from dotenv import load_dotenv

load_dotenv()

DB_HOST = "127.0.0.1"  # Cloud SQL Auth Proxy tunnel — local dev only
DB_PORT = 5433
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

EMBEDDING_BATCH_SIZE = 200  # stays under Vertex's 250-per-request cap


def _embed_in_batches(texts: list[str]) -> list[list[float]]:
    """Embed a large list of chunk texts in batches, respecting Vertex's
    per-request limit, and return all vectors in original order."""
    vectors = []
    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i:i + EMBEDDING_BATCH_SIZE]
        vectors.extend(embed_chunks(batch))
    return vectors


def insert_document(conn, source_name: str, shards: list) -> None:
    """Process one source document end-to-end: parent sections → DB,
    child chunks → DB, in a single transaction per document."""
    tier = get_authority_tier(source_name)

    page_texts = extract_page_texts(shards)
    sections = build_parent_sections(page_texts)

    print(f"{source_name}: {len(sections)} parent sections")

    with conn.cursor() as cur:
        for section in sections:
            # Insert the parent section, using its start page as the
            # section's representative page number.
            cur.execute(
                """
                INSERT INTO document_sections
                    (source_document, page_number, authority_tier, section_text)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
                """,
                (source_name, section["start_page"], tier, section["text"]),
            )
            section_id = cur.fetchone()[0]

            # Split into child chunks (page-aware) and embed them all.
            chunks = split_into_child_chunks(section)
            chunk_texts = [c["text"] for c in chunks]
            vectors = _embed_in_batches(chunk_texts)

            for chunk, vector in zip(chunks, vectors):
                cur.execute(
                    """
                    INSERT INTO document_chunks
                        (section_id, source_document, page_number, authority_tier, chunk_text, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    (section_id, source_name, chunk["page_number"], tier, chunk["text"], vector),
                )
                # search_vector is GENERATED ALWAYS — never inserted directly,
                # Postgres computes it from chunk_text automatically.

    conn.commit()
    print(f"{source_name}: inserted {len(sections)} sections and their chunks.")


if __name__ == "__main__":
    documents = load_existing_batch_output()

    conn = psycopg.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
    )

    try:
        for source_name, shards in documents.items():
            insert_document(conn, source_name, shards)
    finally:
        conn.close()

    print("\nAll documents inserted.")