import os
import psycopg
from retrieval import embed_query, vector_search, full_text_search, rrf_fuse, apply_authority_boost

conn = psycopg.connect(
    host="127.0.0.1", port=5433,
    dbname="budgetsense", user="budgetsense_app", password=os.environ["DB_PASSWORD"],
)

question = "What is the WATO tax offset amount?"
query_vec = embed_query(question)

print("--- Vector search ---")
results = vector_search(conn, query_vec, top_k=5)
for row in results:
    chunk_id, section_id, chunk_text, source_doc, page, tier, distance = row
    print(f"[{distance:.4f}] {source_doc} p.{page} ({tier})")
    print(f"  {chunk_text[:150]}...\n")



print("--- Full-text search ---")
ft_results = full_text_search(conn, question, top_k=5)
for row in ft_results:
    chunk_id, section_id, chunk_text, source_doc, page, tier, rank = row
    print(f"[{rank:.4f}] {source_doc} p.{page} ({tier})")
    print(f"  {chunk_text[:150]}...\n")



print("--- RRF Fused ---")
fused = rrf_fuse(results, ft_results, top_k=5)
for row, score in fused:
    chunk_id, section_id, chunk_text, source_doc, page, tier, _ = row
    print(f"[{score:.5f}] {source_doc} p.{page} ({tier})")
    print(f"  {chunk_text[:150]}...\n")



print("--- Authority-boosted ---")
boosted = apply_authority_boost(fused)
for row, score in boosted:
    chunk_id, section_id, chunk_text, source_doc, page, tier, _ = row
    print(f"[{score:.5f}] {source_doc} p.{page} ({tier})")
    print(f"  {chunk_text[:150]}...\n")

conn.close()