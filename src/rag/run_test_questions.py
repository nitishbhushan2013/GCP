import os
import psycopg
from retrieval import embed_query, retrieve, vector_search

from dotenv import load_dotenv

load_dotenv()

DB_HOST = "127.0.0.1"  # Cloud SQL Auth Proxy tunnel — local dev only
DB_PORT = 5433
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

conn = psycopg.connect(
    host="127.0.0.1", port=5433,
    dbname="budgetsense", user="budgetsense_app", password=os.environ["DB_PASSWORD"],
)

TEST_QUESTIONS = [
    "What is the WATO tax offset amount?",
    "What is the instant tax deduction amount for working Australians?",
    "What is the fuel excise reduction?",
    "What is the underlying cash balance forecast?",
    "What is the gas reservation percentage?",
    "What is the Budget's plan for Mars colonization?",  # negative control
]

for question in TEST_QUESTIONS:
    print(f"\n{'='*80}\nQ: {question}\n{'='*80}")

    query_vec = embed_query(question)
    vector_results = vector_search(conn, query_vec, top_k=5)
    top_distance = vector_results[0][-1]
    print(f"Top vector distance: {top_distance:.4f}")

    boosted, parents = retrieve(conn, question, top_k=5)
  
    print("\n-- Top boosted chunks --")
    for row, score in boosted[:3]:
        _, _, chunk_text, source_doc, page, tier, _ = row
        print(f"[{score:.5f}] {source_doc} p.{page} ({tier})")
        print(f"  {chunk_text[:120]}...")

    print("\n-- Parent sections retrieved --")
    for section_id, source_doc, page, tier, section_text in parents:
        print(f"Section {section_id}: {source_doc} p.{page} ({tier})")

conn.close()