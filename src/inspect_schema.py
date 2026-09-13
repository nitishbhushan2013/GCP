"""
Epic 6 / Phase B / B7 prep — Inspect document_sections and document_chunks
schema before writing insert logic.
"""

import os
import psycopg

DB_HOST = "127.0.0.1"
DB_PORT = 5433
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

if __name__ == "__main__":
    conn = psycopg.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
    )
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_name IN ('document_sections', 'document_chunks')
            ORDER BY table_name, ordinal_position;
        """)
        for row in cur.fetchall():
            print(row)

        cur.execute("""
            SELECT column_name, is_generated, generation_expression
            FROM information_schema.columns
            WHERE table_name = 'document_chunks' AND column_name = 'search_vector';
        """)
        print(cur.fetchall())

        cur.execute("SELECT id, page_number, authority_tier, LEFT(chunk_text, 60) FROM document_chunks LIMIT 3;")
        for row in cur.fetchall():
            print(row)

        cur.execute("SELECT id, embedding IS NOT NULL, vector_dims(embedding) FROM document_chunks LIMIT 3;")
        for row in cur.fetchall():
            print(row)
    conn.close()