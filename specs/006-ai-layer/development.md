# Development Sequence: Spec 006 — AI Layer

This is the working checklist for building Epic 6, in strict execution order. Update
the status marker as each step completes. This is a living document during active
development — once the Epic is done, its findings get folded into
`specs/006-ai-layer/runbook.md` as the permanent record.

Status legend: ⬜ Not started · 🔄 In progress · ✅ Done

## Phase A — Infrastructure (manual, via Console)

- [✅] A1. Create Cloud Storage bucket (`budgetsense-gcp-prod-docs`), private, `australia-southeast1`
- [✅] A2. Upload 3 source PDFs (bp1, bp2, budget-overview) to the bucket
- [✅] A3. Grant `budgetsense-run-sa` → Storage Object Viewer on the bucket
- [✅] A4. Enable `pgvector` extension on `budgetsense-db` (`CREATE EXTENSION vector;`)
- [✅] A5. Create `document_sections` and `document_chunks` tables (hierarchical, per ADR-005)
- [✅] A6. Create vector (ivfflat) and full-text (GIN) indexes on `document_chunks`
- [✅] A7. Create Document AI processor (`budgetsense-ocr`, Document OCR type, region `us`)
- [✅] A8. Copy the Processor ID for use in ingestion code
- [✅] A9. Grant `budgetsense-run-sa` → Document AI API User (`roles/documentai.apiUser`)
- [✅] A10. Grant `budgetsense-run-sa` → Vertex AI User (`roles/aiplatform.user`)

## Phase B — Ingestion Pipeline (code)

- [✅]] B1. Write script: read each PDF from Cloud Storage
- [✅] B2. Write script: send each PDF to Document AI, get parsed text back
- [✅] B3. Write parent-section splitting logic (~1,500-2,500 tokens per section, page-aware)
- [✅] B4. Write child-chunk splitting logic within each section (~150-250 tokens, with overlap)
- [✅] B5. Assign `authority_tier` per source document (BP1/BP2 = highest tier, Overview = summary tier)
- [✅ B6. Write embedding generation call (Vertex AI `text-embedding-005`, `RETRIEVAL_DOCUMENT` task type, confirm 768-dim output)
- [✅] B7. Write insert logic: parent section → `document_sections`, then its child chunks (with `section_id`, embedding, metadata) → `document_chunks`
- [✅] B8. Run the full ingestion script against all 3 PDFs
- [✅ B9. Verify row counts and spot-check a few sections/chunks directly in Cloud SQL Studio

## Phase C — Hybrid Retrieval (code)

- [✅] C1. Write vector similarity query over `document_chunks` (cosine distance via `embedding <=> query_embedding`, `RETRIEVAL_QUERY` task type for the question's embedding)
- [✅] C2. Write full-text search query (`search_vector @@ plainto_tsquery(...)`)
- [✅] C3. Combine both via Reciprocal Rank Fusion (RRF)
- [⬜] C4. Apply `authority_tier` as a ranking boost (not a hard filter)
- [⬜] C5. Write parent lookup: matched chunk → fetch its `document_sections` row via `section_id`
- [⬜] C6. Manually test retrieval against the 5 known test questions — confirm sensible chunks AND correct parent sections return before touching generation

## Phase D — Grounded Generation (code)

- [⬜] D1. Write Gemini prompt template: answer only from retrieved parent section(s), cite the specific child chunk/page, say "not found" if no good match
- [⬜] D2. Wire retrieved parent section(s) + question into the Gemini call
- [⬜] D3. Parse Gemini's response into: answer text + citation list (source doc, page, authority tier)

## Phase E — Endpoint & Deployment

- [⬜] E1. Add `POST /query` endpoint to `src/main.py`
- [⬜] E2. Wire endpoint: question in → retrieval (Phase C) → generation (Phase D) → response out
- [⬜] E3. Build and push new Docker image to Artifact Registry (new tag, e.g. `:v2`)
- [⬜] E4. Deploy new Cloud Run revision with the updated image

## Phase F — Verification (per Spec 006 acceptance criteria)

- [⬜] F1. Run all 5 test questions against the live `/query` endpoint
- [⬜] F2. Verify each citation actually supports its claim (manual check against source PDF text)
- [⬜] F3. Confirm the negative test (Mars colonization question) returns "not found," not a fabrication
- [⬜] F4. Write `specs/006-ai-layer/runbook.md` with final results, chunking approach used, and actual test outputs

## Phase G — Documentation & Cleanup

- [✅] G1. Log ADR-005: hierarchical (parent-child) chunking
- [⬜] G2. Log ADR-006: Document AI region exception (`us`/`eu`, not `australia-southeast1`) — data residency deviation for this one service
- [⬜] G3. Update `docs/PRD.md` Epic 6 status to ✅ Done
- [⬜] G4. Write the short Epic 6 takeaways + interview pitch doc (per the standing preference)

---

**Where we are right now: Phase C, step C4** — apply authority_tier as a ranking boost.
