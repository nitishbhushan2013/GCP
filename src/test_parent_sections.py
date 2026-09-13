"""
Epic 6 / Phase B / B3 — Test parent-section splitting against real docs.
"""

from parse_pdfs_batch import batch_process_pdfs
from google.cloud import documentai_v1 as documentai

TARGET_MIN_TOKENS = 1500
TARGET_MAX_TOKENS = 2500


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def extract_page_texts(documents: list[documentai.Document]) -> list[tuple[int, str]]:
    """Extract (global_page_number, page_text) pairs across one or more
    Document shards, using each page's own page_number field so ordering
    stays correct regardless of how many shards a file was split into."""
    pages = []
    for doc in documents:
        full_text = doc.text
        for page in doc.pages:
            segments = page.layout.text_anchor.text_segments
            page_text = "".join(
                full_text[seg.start_index:seg.end_index] for seg in segments
            )
            pages.append((page.page_number, page_text))
    pages.sort(key=lambda p: p[0])
    return pages


def build_parent_sections(page_texts: list[tuple[int, str]]) -> list[dict]:
    """Group consecutive pages into parent sections of ~1,500-2,500 tokens,
    always breaking on a page boundary. Each section now also carries its
    own list of (page_number, page_text) pairs, so child chunks (B4) can
    determine exactly which page they start on."""
    sections = []
    current_text = ""
    current_pages = []
    current_start_page = None

    for page_num, page_text in page_texts:
        if current_start_page is None:
            current_start_page = page_num

        current_text += page_text
        current_pages.append((page_num, page_text))
        token_count = estimate_tokens(current_text)

        if token_count >= TARGET_MIN_TOKENS:
            sections.append({
                "text": current_text,
                "pages": current_pages,
                "start_page": current_start_page,
                "end_page": page_num,
                "estimated_tokens": token_count,
            })
            current_text = ""
            current_pages = []
            current_start_page = None

    if current_text:
        if sections:
            sections[-1]["text"] += current_text
            sections[-1]["pages"].extend(current_pages)
            sections[-1]["end_page"] = page_texts[-1][0]
            sections[-1]["estimated_tokens"] = estimate_tokens(sections[-1]["text"])
        else:
            sections.append({
                "text": current_text,
                "pages": current_pages,
                "start_page": current_start_page,
                "end_page": page_texts[-1][0],
                "estimated_tokens": estimate_tokens(current_text),
            })

    return sections


# test_parent_sections.py
if __name__ == "__main__":
    documents = batch_process_pdfs()

    for filename, shards in documents.items():
        total_pages = sum(len(doc.pages) for doc in shards)
        print(f"\n=== {filename} ({total_pages} pages, {len(shards)} shard(s)) ===")
        page_texts = extract_page_texts(shards)
        sections = build_parent_sections(page_texts)

        print(f"Split into {len(sections)} parent sections:")
        for i, section in enumerate(sections, start=1):
            over_budget = section["estimated_tokens"] > TARGET_MAX_TOKENS
            flag = " ⚠ over 2,500 target" if over_budget else ""
            print(
                f"  Section {i}: pages {section['start_page']}-{section['end_page']}, "
                f"~{section['estimated_tokens']:,} tokens{flag}"
            )