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
3. Otherwise - if at least one sub-topic IS supported - address each supported 
   sub-topic as its own short point. For any remaining sub-topic that has no 
   support, note that briefly in one line rather than omitting it silently, but 
   only under this instruction, never as a way to avoid instruction 2's exact 
   phrase when it applies.
4. Every factual claim must be traceable to a specific source below. Reference 
   each claim with its source label, e.g. [Source 1, p.35].
5. Do not combine or infer figures that are not explicitly stated together in 
   the same source.
6. Keep each sub-topic's point concise - this should read as a short, organized 
   answer, not an essay, even when it covers multiple sub-topics.

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
def generate_answer(question: str, sub_questions: list[str], parent_sections: list) -> str:
    prompt = build_prompt(question, sub_questions, parent_sections)
    client = genai.Client(vertexai=True, project="budgetsense-gcp-prod", location="us-central1")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=GenerateContentConfig(temperature=0.0),
    )
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
