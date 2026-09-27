from google import genai
from google.genai.types import GenerateContentConfig


PROMPT_TEMPLATE = """You are answering questions about the Australian Federal Budget using ONLY the source material provided below. Do not use any outside knowledge, 
even if you know the answer from elsewhere.

SOURCE MATERIAL:
{context}

ORIGINAL QUESTION: {question}

This question was broken down into the following sub-topics, each independently 
researched against the source material above:
{sub_questions_list}

Instructions:
1. Answer using ONLY the source material above.
2. If NONE of the sub-topics above are supported by any source material, respond 
   with exactly this phrase and nothing else: "Not found in the provided budget 
   documents."
3a. If the source material spans multiple distinct categories or programs (e.g. 
   tax measures, grants, loan schemes, R&D incentives are different categories - 
   don't group them under one heading), use a separate markdown heading (### 
   Category Name) for each one - do not put more than one genuinely distinct 
   category under a single heading. Use one level of bullet points under each 
   heading; never nest a second bullet level or use inline asterisks as sub-points 
   within a bullet's text. If the question and source material are genuinely 
   narrow (a single fact or figure), skip headings entirely and answer in a 
   sentence or two.
   Each heading must appear on its own line, with a line break before it - never 
    immediately after other text or punctuation on the same line (e.g. never 
    "...as follows: ### Category Name" - put a line break before ### instead).
3b. Before the first heading, include one brief introductory sentence that 
   directly acknowledges the question asked (e.g. "Here's what the Budget 
   provides for small businesses, grouped by category:") - don't jump straight 
   into the first heading with no framing.   
4. Every factual claim must be traceable to a specific source below. Reference 
   each claim with its source label, e.g. [Source 1, p.35].
5. Do not combine or infer figures that are not explicitly stated together in 
   the same source.
6. Keep each sub-topic's point concise - this should read as a short, organized 
   answer, not an essay, even when it covers multiple sub-topics.
7. After all category sections, add a final heading "### Next Steps" with 2 to 
   4 short, concrete, procedural bullet points telling the citizen what they 
   could look into or do next based on what's in the source material - e.g. 
   checking specific eligibility criteria mentioned above, using a relevant 
   government resource or tool, or consulting a registered tax agent or 
   financial adviser for their specific situation. These must stay factual and 
   procedural - never a personalized recommendation ("you should do X") and 
   never inventing a URL or resource not already grounded in the source 
   material or general knowledge of standard government services (ATO, 
   Services Australia). If the question and answer were genuinely narrow (a 
   single fact, no categories), skip this section entirely.

ANSWER:"""


def build_prompt(question: str, sub_questions: list[str], parent_sections: list) -> str:
    context_blocks = []
    for i, (section_id, source_doc, page, tier, section_text) in enumerate(parent_sections, start=1):
        context_blocks.append(
            f"[Source {i}, {source_doc} p.{page}, {tier} tier]\n{section_text}"
        )
    context = "\n\n".join(context_blocks)
    sub_questions_list = "\n".join(f"- {sq}" for sq in sub_questions)
    return PROMPT_TEMPLATE.format(
        context=context, question=question, sub_questions_list=sub_questions_list
    )

"""
temperature=0.0 — Zero temperature makes output as deterministic and literal as possible, minimizing the model's tendency to paraphrase loosely 
                or fill gaps with plausible-sounding but unsupported detail. It brings the model's output closer to a strict extraction from the provided context, 
                        which is crucial for factual accuracy in this task.
"""
def generate_answer(question: str, sub_questions: list[str], parent_sections: list, usage_log: list = None) -> str:
    prompt = build_prompt(question, sub_questions, parent_sections)
    client = genai.Client(vertexai=True, project="budgetsense-gcp-prod", location="us-central1")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=GenerateContentConfig(temperature=0.0),
    )
    if usage_log is not None:
        usage = getattr(response, "usage_metadata", None)
        usage_log.append({
            "input_tokens": getattr(usage, "prompt_token_count", 0) or 0,
            "output_tokens": getattr(usage, "candidates_token_count", 0) or 0,
        })
    return response.text

import re

def parse_response(raw_answer: str, parent_sections: list) -> dict:
    # Matches one whole [Source ...] bracket, however many citations are inside it
    bracket_pattern = r"\[Source[^\]]+\]"
    # Extracts individual "Source N" numbers from inside a matched bracket
    number_pattern = r"Source (\d+)"
    PUBLIC_DOCS_BASE_URL = "https://storage.googleapis.com/budgetsense-gcp-prod-docs-public"
    all_brackets = re.findall(bracket_pattern, raw_answer)
    cited_source_nums = sorted(set(
        int(n) for bracket in all_brackets for n in re.findall(number_pattern, bracket)
    ))

    citations = []
    for num in cited_source_nums:
        idx = num - 1
        if 0 <= idx < len(parent_sections):
            section_id, source_doc, page, tier, _ = parent_sections[idx]
            citations.append({
                "source_document": source_doc,
                "page_number": page,
                "authority_tier": tier,
                 "url": f"{PUBLIC_DOCS_BASE_URL}/{source_doc}.pdf#page={page}",
            })

    clean_answer = re.sub(bracket_pattern, "", raw_answer)
    clean_answer = re.sub(r"[,\s]+([.,])", r"\1", clean_answer)
    clean_answer = re.sub(r"\s{2,}", " ", clean_answer).strip()

    not_found = "not found in the provided budget documents" in raw_answer.lower()

    return {
        "answer": clean_answer,
        "citations": citations,
        "not_found": not_found,
    }
