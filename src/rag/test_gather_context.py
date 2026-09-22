import os
import psycopg
from dotenv import load_dotenv

from agent import decompose_question, multi_hop_retrieve, check_sufficiency

load_dotenv()

DB_HOST = os.environ.get("DB_HOST")  # Cloud SQL Auth Proxy tunnel — local dev only
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

conn = psycopg.connect(
    host=DB_HOST, port=DB_PORT,
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
)

TEST_QUESTIONS = [
    "What is the WATO tax offset amount?",
    "Our family has run a discretionary trust for 20 years - what changes under this budget and when do we need to act?",
    "What is the best way to plan my finances to reduce my tax, including for a working couple with kids?",
    "What is the Budget's plan for Mars colonization?",
]

for question in TEST_QUESTIONS:
    print(f"\n{'='*80}\nQ: {question}\n{'='*80}")

    sub_questions = decompose_question(question)
    print(f"Sub-questions ({len(sub_questions)}): {sub_questions}")

    parents = multi_hop_retrieve(conn, sub_questions, top_k=5)
    print(f"Initial pass: {len(parents)} section(s)")

    sufficient, gap_question = check_sufficiency(question, sub_questions, parents)
    print(f"Sufficiency verdict: {sufficient} | Gap question: {gap_question}")

    if not sufficient and gap_question:
        gap_parents = multi_hop_retrieve(conn, [gap_question], top_k=5)
        seen_ids = {p[0] for p in parents}
        added = [p for p in gap_parents if p[0] not in seen_ids]
        parents.extend(added)
        print(f"Retry added {len(added)} new section(s)")

    print(f"Final: {len(parents)} section(s)")
    for section_id, source_doc, page, tier, section_text in parents:
        print(f"  Section {section_id}: {source_doc} p.{page} ({tier})")

conn.close()


'''Output from running this test script:
================================================================================
================================================================================
Q: What is the WATO tax offset amount?
================================================================================
Sub-questions (1): ['What is the WATO tax offset amount?']
Initial pass: 5 section(s)
Sufficiency verdict: True | Gap question: None
Final: 5 section(s)
  Section 100: womens-budget-statement-2026-27 p.51 (primary)
  Section 152: Strategy and Outlook_2026-27 p.33 (primary)
  Section 288: tax-explainers-new-tax-cuts-workers p.1 (summary)
  Section 191: Strategy and Outlook_2026-27 p.169 (primary)
  Section 270: budget-overview-2026-27 p.20 (summary)

================================================================================
Q: Our family has run a discretionary trust for 20 years - what changes under this budget and when do we need to act?
================================================================================
Sub-questions (1): ['What changes are proposed for discretionary trusts in the budget, and what are their effective dates or implementation timelines?']
Initial pass: 3 section(s)
Sufficiency verdict: False | Gap question: What specific budget measures or legislative changes are proposed that directly impact the taxation or operation of discretionary trusts?
Retry added 2 new section(s)
Final: 5 section(s)
  Section 190: Strategy and Outlook_2026-27 p.166 (primary)
  Section 51: Budget Measures_2026-27 p.36 (primary)
  Section 38: Agency Resourcing_2026_27_consolidated p.198 (primary)
  Section 43: Budget Measures_2026-27 p.1 (primary)
  Section 283: tax-explainers-minimum-tax-discretionary-trusts p.1 (summary)

================================================================================
Q: What is the best way to plan my finances to reduce my tax, including for a working couple with kids?
================================================================================
Sub-questions (3): ['What tax offsets, deductions, or concessions are available to individuals in Australia?', 'What specific tax benefits, offsets, ordeductions are available for working couples in Australia?', 'What specific tax benefits, offsets, or payments are available for families with childrenin Australia?']
Initial pass: 10 section(s)
Sufficiency verdict: False | Gap question: What tax benefits, offsets, or deductions are specifically designed for working couples in Australia?
Retry added 0 new section(s)
Final: 10 section(s)
  Section 288: tax-explainers-new-tax-cuts-workers p.1 (summary)
  Section 182: Strategy and Outlook_2026-27 p.138 (primary)
  Section 106: womens-budget-statement-2026-27 p.71 (primary)
  Section 273: budget-overview-2026-27 p.33 (summary)
  Section 154: Strategy and Outlook_2026-27 p.38 (primary)
  Section 195: Strategy and Outlook_2026-27 p.183 (primary)
  Section 84: Budget Measures_2026-27 p.150 (primary)
  Section 156: Strategy and Outlook_2026-27 p.44 (primary)
  Section 190: Strategy and Outlook_2026-27 p.166 (primary)
  Section 207: Strategy and Outlook_2026-27 p.231 (primary)

================================================================================
Q: What is the Budget's plan for Mars colonization?
================================================================================
Sub-questions (1): ['What plans or funding related to Mars colonization are included in the Australian Federal Budget?']
Initial pass: 5 section(s)
Sufficiency verdict: False | Gap question: Does the Australian Federal Budget 2026-27 include any allocations or plans for Mars colonization or relatedspace exploration programs?
Retry added 1 new section(s)
Final: 6 section(s)
  Section 151: Strategy and Outlook_2026-27 p.30 (primary)
  Section 43: Budget Measures_2026-27 p.1 (primary)
  Section 107: Federal Financial Relations_2026-27 p.1 (primary)
  Section 44: Budget Measures_2026-27 p.10 (primary)
  Section 276: budget-overview-2026-27 p.46 (summary)
  Section 142: Strategy and Outlook_2026-27 p.1 (primary)
'''
