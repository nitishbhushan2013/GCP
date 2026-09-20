import os
import psycopg
from retrieval import embed_query, vector_search, full_text_search, rrf_fuse, apply_authority_boost, fetch_parent_sections
from generation import generate_answer, parse_response

from dotenv import load_dotenv

load_dotenv()

DB_HOST = "127.0.0.1"  # Cloud SQL Auth Proxy tunnel — local dev only
DB_PORT = 5433
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

conn = psycopg.connect(
    host="127.0.0.1", port=5433,
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
)


#question = "What is the WATO tax offset amount?"
question = "What is the best way to plan my finances to reduce my tax, including for a working couple with kids?"
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
parsed = parse_response(answer, parents)
print(f"\n--- Parsed ---")
print(f"Answer: {parsed['answer']}")
print(f"Citations: {parsed['citations']}")
print(f"Not found flag: {parsed['not_found']}")


conn.close()