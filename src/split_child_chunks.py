"""
Epic 6 / Phase B / B4 — Child-chunk splitting within each parent section
(page-aware).
"""

CHUNK_TARGET_TOKENS = 200
CHUNK_OVERLAP_TOKENS = 40
CHARS_PER_TOKEN = 4


def _build_page_boundaries(pages: list[tuple[int, str]]) -> list[tuple[int, int, int]]:
    """Given a section's (page_number, page_text) list, return
    (start_offset, end_offset, page_number) triples describing where each
    page's text falls within the section's combined string."""
    boundaries = []
    offset = 0
    for page_num, page_text in pages:
        start = offset
        end = offset + len(page_text)
        boundaries.append((start, end, page_num))
        offset = end
    return boundaries


def _page_at_offset(boundaries: list[tuple[int, int, int]], position: int) -> int:
    """Find which page a given character offset falls on. Falls back to
    the last known page if position lands past the end (can happen due
    to whitespace-snapping at a section's tail)."""
    for start, end, page_num in boundaries:
        if start <= position < end:
            return page_num
    return boundaries[-1][2]


def split_into_child_chunks(section: dict) -> list[dict]:
    """Split one parent section into overlapping child chunks. Each
    returned chunk is a dict with 'text' and 'page_number' (the page the
    chunk actually starts on, not the section's overall start page)."""
    section_text = section["text"]
    boundaries = _build_page_boundaries(section["pages"])

    chunk_chars = CHUNK_TARGET_TOKENS * CHARS_PER_TOKEN
    overlap_chars = CHUNK_OVERLAP_TOKENS * CHARS_PER_TOKEN
    step_chars = chunk_chars - overlap_chars

    if step_chars <= 0:
        raise ValueError("CHUNK_OVERLAP_TOKENS must be smaller than CHUNK_TARGET_TOKENS")

    chunks = []
    position = 0
    text_length = len(section_text)

    while position < text_length:
        end = min(position + chunk_chars, text_length)

        if end < text_length:
            next_space = section_text.find(" ", end)
            if next_space != -1:
                end = next_space

        chunk_text = section_text[position:end].strip()
        if chunk_text:
            chunks.append({
                "text": chunk_text,
                "page_number": _page_at_offset(boundaries, position),
            })

        if end >= text_length:
            break

        position += step_chars

    return chunks


if __name__ == "__main__":
    from parse_pdfs_batch import batch_process_pdfs
    from test_parent_sections import extract_page_texts, build_parent_sections

    documents = batch_process_pdfs()

    for filename, shards in documents.items():
        page_texts = extract_page_texts(shards)
        sections = build_parent_sections(page_texts)

        print(f"\n=== {filename}: {len(sections)} parent sections ===")
        total_chunks = 0
        for i, section in enumerate(sections[:2], start=1):  # just first 2 sections as a spot-check
            chunks = split_into_child_chunks(section["text"])
            total_chunks += len(chunks)
            print(f"  Section {i} ({section['estimated_tokens']} tokens) → {len(chunks)} chunks")
            for j, chunk in enumerate(chunks[:3], start=1):  # first 3 chunks per section
                print(f"    Chunk {j}: {len(chunk)} chars — \"{chunk[:60]}...\"")