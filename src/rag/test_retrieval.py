import os
import psycopg
from retrieval import embed_query, vector_search, full_text_search, rrf_fuse, apply_authority_boost, fetch_parent_sections
from generation import generate_answer

conn = psycopg.connect(
    host="127.0.0.1", port=5433,
    dbname="budgetsense", user="budgetsense_app", password=os.environ["DB_PASSWORD"],
)


question = "What is the WATO tax offset amount?"
#question = "I run a café with $800K turnover. What Budget measures can help my cash flow right now?"
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


print("--- Parent Sections ---")
parents = fetch_parent_sections(conn, boosted)
for section_id, source_doc, page, tier, section_text in parents:
    print(f"Section {section_id}: {source_doc} p.{page} ({tier})")
    print(f"  {section_text[:200]}...\n")

answer = generate_answer(question, parents)
print(f"\n--- Generated Answer ---\n{answer}")

conn.close()