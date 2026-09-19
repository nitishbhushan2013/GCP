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
