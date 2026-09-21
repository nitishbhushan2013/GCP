import os
import psycopg
from dotenv import load_dotenv

from agent import decompose_question, multi_hop_retrieve

load_dotenv()

DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

conn = psycopg.connect(
    host="127.0.0.1", port=5433,
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
)

TEST_QUESTIONS = [
    "Our family has run a discretionary trust for 20 years - what changes under this budget and when do we need to act?",
    "What is the best way to plan my finances to reduce my tax, including for a working couple with kids?",
]

for question in TEST_QUESTIONS:
    print(f"\n{'='*80}\nQ: {question}\n{'='*80}")

    sub_questions = decompose_question(question)
    print(f"\nDecomposed into {len(sub_questions)} sub-question(s):")
    for i, sq in enumerate(sub_questions, start=1):
        print(f"  {i}. {sq}")

    parents = multi_hop_retrieve(conn, sub_questions, top_k=5)
    print(f"\n-- Deduped parent sections retrieved: {len(parents)} --")
    for section_id, source_doc, page, tier, section_text in parents:
        print(f"Section {section_id}: {source_doc} p.{page} ({tier})")

conn.close()


'''
Output from running this test script:
================================================================================
Q: Our family has run a discretionary trust for 20 years - what changes under this budget and when do we need to act?
================================================================================
Decomposed into 2 sub-question(s):
  1. What changes related to discretionary trusts are included in the Australian Federal Budget?
  2. What are the effective dates or implementation timelines for any budget changes affecting discretionary trusts?

-- Deduped parent sections retrieved: 7 --
Section 38: Agency Resourcing_2026_27_consolidated p.198 (primary)
Section 190: Strategy and Outlook_2026-27 p.166 (primary)
Section 142: Strategy and Outlook_2026-27 p.1 (primary)
Section 51: Budget Measures_2026-27 p.36 (primary)
Section 283: tax-explainers-minimum-tax-discretionary-trusts p.1 (summary)
Section 225: Strategy and Outlook_2026-27 p.305 (primary)
Section 222: Strategy and Outlook_2026-27 p.297 (primary)

================================================================================
Q: What is the best way to plan my finances to reduce my tax, including for a working couple with kids?
================================================================================

Decomposed into 3 sub-question(s):
  1. What are the current tax offsets and deductions available to individuals in Australia?
  2. What tax benefits, offsets, or deductions are available for working couples with dependent children?
  3. What are the tax rules and contribution limits for superannuation contributions?

-- Deduped parent sections retrieved: 12 --
Section 288: tax-explainers-new-tax-cuts-workers p.1 (summary)
Section 182: Strategy and Outlook_2026-27 p.138 (primary)
Section 188: Strategy and Outlook_2026-27 p.160 (primary)
Section 273: budget-overview-2026-27 p.33 (summary)
Section 195: Strategy and Outlook_2026-27 p.183 (primary)
Section 154: Strategy and Outlook_2026-27 p.38 (primary)
Section 191: Strategy and Outlook_2026-27 p.169 (primary)
Section 100: womens-budget-statement-2026-27 p.51 (primary)
Section 239: Strategy and Outlook_2026-27 p.348 (primary)
Section 101: womens-budget-statement-2026-27 p.54 (primary)
Section 243: Strategy and Outlook_2026-27 p.362 (primary)
Section 274: budget-overview-2026-27 p.38 (summary)
'''