from google import genai
from google.genai.types import GenerateContentConfig


PROMPT_TEMPLATE = """You are answering questions about the Australian Federal Budget using ONLY the source material provided below. Do not use any outside knowledge, 
even if you know the answer from elsewhere.

SOURCE MATERIAL:
{context}

QUESTION: {question}

Instructions:
1. Answer using ONLY the source material above. If the answer is not clearly supported by it, respond exactly: "Not found in the provided budget documents."
2. Every factual claim in your answer must be traceable to a specific source below. Reference each claim with its source label, e.g. [Source 1, p.35].
3. Do not combine or infer figures that are not explicitly stated together in the same source.
4. Keep the answer concise - a few sentences, not a full essay.

ANSWER:"""


def build_prompt(question: str, parent_sections: list) -> str:
    context_blocks = []
    for i, (section_id, source_doc, page, tier, section_text) in enumerate(parent_sections, start=1):
        context_blocks.append(
            f"[Source {i}, {source_doc} p.{page}, {tier} tier]\n{section_text}"
        )
    context = "\n\n".join(context_blocks)
    return PROMPT_TEMPLATE.format(context=context, question=question)

"""
temperature=0.0 — Zero temperature makes output as deterministic and literal as possible, minimizing the model's tendency to paraphrase loosely 
                or fill gaps with plausible-sounding but unsupported detail. It brings the model's output closer to a strict extraction from the provided context, 
                        which is crucial for factual accuracy in this task.
"""
def generate_answer(question: str, parent_sections: list) -> str:
    prompt = build_prompt(question, parent_sections)
    client = genai.Client(vertexai=True, project="budgetsense-gcp-prod", location="us-central1")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=GenerateContentConfig(temperature=0.0),
    )
    return response.text

import re

def parse_response(raw_answer: str, parent_sections: list) -> dict:
    citation_pattern = r"\[Source (\d+),?\s*p\.(\d+)\]"
    matches = re.findall(citation_pattern, raw_answer)

# cited_source_nums deduplicates and sorts — if Gemini cites Source 1 twice in one answer, we don't want it listed twice in the structured output.
    cited_source_nums = sorted(set(int(num) for num, _ in matches))

    citations = []
    for num in cited_source_nums:
        idx = num - 1
        if 0 <= idx < len(parent_sections):
            section_id, source_doc, page, tier, _ = parent_sections[idx]
            citations.append({
                "source_document": source_doc,
                "page_number": page,
                "authority_tier": tier,
            })

    clean_answer = re.sub(citation_pattern, "", raw_answer)
    clean_answer = re.sub(r"[,\s]+([.,])", r"\1", clean_answer)  # collapse leftover commas/spaces before punctuation
    clean_answer = re.sub(r"\s{2,}", " ", clean_answer).strip()  # collapse any double-spaces left behind

    not_found = "not found in the provided budget documents" in raw_answer.lower()

    return {
        "answer": clean_answer,
        "citations": citations,
        "not_found": not_found,
    }
