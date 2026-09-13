"""
Epic 6 / Phase B / B6 — Quick test of embedding generation against real chunks.
"""

from parse_pdfs_batch import batch_process_pdfs
from test_parent_sections import extract_page_texts, build_parent_sections
from split_child_chunks import split_into_child_chunks
from embed_chunks import embed_chunks

if __name__ == "__main__":
    documents = batch_process_pdfs()

    # Just grab the first section's chunks from budget-overview — smallest
    # document, fastest to test against.
    shards = documents["budget-overview-2026-27"]
    page_texts = extract_page_texts(shards)
    sections = build_parent_sections(page_texts)
    chunks = split_into_child_chunks(sections[0])  # now takes the section dict
    chunk_texts = [c["text"] for c in chunks]      # embed_chunks() still wants plain strings
    print(f"Embedding {len(chunk_texts)} chunks from section 1...")
    vectors = embed_chunks(chunk_texts)

    print(f"Got {len(vectors)} embeddings, each {len(vectors[0])}-dim")
    print(f"First vector, first 5 values: {vectors[0][:5]}")
    print(f"Second vector, first 5 values: {vectors[1][:5]}")