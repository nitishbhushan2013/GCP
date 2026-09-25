import os
import psycopg
from dotenv import load_dotenv

from agent import gather_context
from generation import generate_answer, parse_response

load_dotenv()

DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

conn = psycopg.connect(
    host="127.0.0.1", port=5433,
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
)

TEST_QUESTIONS = [
    #"What is the WATO tax offset amount?",
    #"Our family has run a discretionary trust for 20 years - what changes under this budget and when do we need to act?",
    #"What is the best way to plan my finances to reduce my tax, including for a working couple with kids?",
    "What is the Budget's plan for Mars colonization?",
]

for question in TEST_QUESTIONS:
    print(f"\n{'='*80}\nQ: {question}\n{'='*80}")

    sub_questions, parents = gather_context(conn, question, top_k=5)
    print(f"Sub-questions ({len(sub_questions)}): {sub_questions}")
    print(f"Sections in pool: {len(parents)}")

    raw_answer = generate_answer(question, sub_questions, parents)
    parsed = parse_response(raw_answer, parents)

    print(f"\n--- RAW ANSWER ---\n{raw_answer}")
    print(f"\n--- PARSED ---")
    print(f"not_found: {parsed['not_found']}")
    print(f"answer: {parsed['answer']}")
    print(f"citations: {len(parsed['citations'])}")
    for c in parsed['citations']:
        print(f"  {c['source_document']} p.{c['page_number']} ({c['authority_tier']})")

conn.close()