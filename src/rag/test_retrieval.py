import os
import psycopg
from retrieval import embed_query, vector_search

conn = psycopg.connect(
    host="127.0.0.1", port=5433,
    dbname="budgetsense", user="budgetsense_app", password=os.environ["DB_PASSWORD"],
)

question = "What is the WATO tax offset amount?"
query_vec = embed_query(question)
results = vector_search(conn, query_vec, top_k=5)

for row in results:
    chunk_id, section_id, chunk_text, source_doc, page, tier, distance = row
    print(f"[{distance:.4f}] {source_doc} p.{page} ({tier})")
    print(f"  {chunk_text[:150]}...\n")

conn.close()