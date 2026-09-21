import json

from google import genai
from google.genai.types import GenerateContentConfig
from retrieval import retrieve

DECOMPOSE_PROMPT_TEMPLATE = """You are the query-planning step of a Q&A system that answers questions about 
the Australian Federal Budget using only the source documents in a retrieval database.

CITIZEN'S QUESTION:
{question}

Break this question down into 1 to 4 focused sub-questions that, together, cover everything the 
citizen is asking about. Each sub-question will be looked up independently against the budget 
documents, so:

1. Each sub-question must be self-contained and answerable on its own, without needing any other 
   sub-question's answer first.
2. Each sub-question must be PURELY FACTUAL - asking what a policy, rate, threshold, date or 
   eligibility rule IS, never what the citizen SHOULD DO. Reword any advice-seeking language 
   ("what should I do", "best way to", "how can I reduce") into a request for the underlying facts 
   (e.g. "what tax offsets/thresholds/eligibility rules apply to X").
3. If the question already asks about a single fact or topic, do not split it - return exactly one 
   sub-question, the original question unchanged (only reworded if it is advice-framed).
4. Do not introduce a topic the original question does not imply.
5. Do not split a timing/effective-date/implementation-timeline question off into its own 
   sub-question when it belongs to the same underlying topic as another sub-question. Budget 
   explainer documents typically state a policy change and its effective date in the same 
   passage, so a question like "what changes and when does it take effect" should stay as ONE 
  sub-question covering both - not two, one for the change and a separate one for the date.

Respond with ONLY a JSON object of this exact shape, no other text:
{{"sub_questions": ["...", "..."]}}"""


def build_decompose_prompt(question: str) -> str:
    return DECOMPOSE_PROMPT_TEMPLATE.format(question=question)


"""
temperature=0.0 - decomposition is a structural/logical task, not a creative one; we want the same
                   question to split the same way every time, and zero temperature keeps Gemini from
                   drifting into extra sub-questions or advice-flavoured wording across runs.
response_mime_type="application/json" - asks Gemini to return raw JSON instead of freeform prose, so
                   parsing here doesn't need the same regex-scraping generation.py uses on answer text -
                   there's no citation-bracket structure to preserve, just a list of strings.
"""
def decompose_question(question: str) -> list[str]:
    prompt = build_decompose_prompt(question)
    client = genai.Client(vertexai=True, project="budgetsense-gcp-prod", location="us-central1")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=GenerateContentConfig(temperature=0.0, response_mime_type="application/json"),
    )

    try:
        parsed = json.loads(response.text)
        sub_questions = [q.strip() for q in parsed.get("sub_questions", []) if q.strip()]
    except (json.JSONDecodeError, AttributeError):
        sub_questions = []

    # Bounded 1-4 per Story 8.1's acceptance criteria; fall back to the original question
    # unchanged if Gemini returned nothing usable, rather than letting an empty list reach retrieval.
    if not sub_questions:
        return [question]
    return sub_questions[:4]

def multi_hop_retrieve(conn, sub_questions: list[str], top_k: int = 5):
    seen_section_ids = set()
    deduped_parents = []

    for sub_question in sub_questions:
        _, parents = retrieve(conn, sub_question, top_k=top_k)
        for parent in parents:
            section_id = parent[0]
            if section_id not in seen_section_ids:
                seen_section_ids.add(section_id)
                deduped_parents.append(parent)

    return deduped_parents