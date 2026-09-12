# Spec 006: Applied AI — RAG Layer

## Status

Draft → Implementing (manual, via Console + code)

## 1. Problem

Epics 1–4 built a secure, observable, privately-networked system — but it doesn't
do anything useful yet. This spec adds the actual product capability: grounded,
cited question-answering over Australian Federal Budget policy documents, mirroring
BudgetSense's original AWS architecture on GCP-native services.

## 2. Requirements

### 2.1 Document Storage (PRD Story 6.1)

- A Cloud Storage bucket holding source budget policy documents (PDFs).
- Bucket in `australia-southeast1`, private (no public access) — same data
  residency and access discipline as the rest of the project.

### 2.2 Document Parsing (PRD Story 6.2)

- Document AI (Document OCR or Layout Parser processor) extracts text and
  structure from each PDF in the bucket.
- Output: clean text per document, chunked into passages suitable for embedding
  (chunk size TBD at implementation time — likely a few hundred tokens per chunk,
  matching common RAG practice).
- Each chunk retains metadata: source document name, page number, and an
  **authority tier** (e.g. Treasury > agency > secondary) — set manually for
  this project's small document set, not auto-classified.

### 2.3 Vector Index (PRD Story 6.3 — see ADR-004 for implementation deviation)

- `pgvector` extension enabled on the existing Cloud SQL instance (`budgetsense-db`).
- A new table storing: chunk text, chunk embedding (vector), source document,
  page number, authority tier.
- Embeddings generated via Vertex AI's embedding model (e.g.
  `text-embedding-004` or current equivalent at implementation time).
- Combined with Postgres native full-text search (`tsvector`/`tsquery`) for a
  BM25-style lexical signal, fused with the vector similarity score (Reciprocal
  Rank Fusion) — the same hybrid approach as BudgetSense's original AWS design.
- Authority tier applied as a ranking weight/boost, not a hard filter — a
  lower-tier source can still surface if it's the best match, just ranked lower.

### 2.4 Grounded Generation (PRD Story 6.4)

- Vertex AI Gemini generates the answer, constrained to only the retrieved chunks
  (retrieved-context-only prompting — the model is instructed not to answer from
  its own general knowledge if the retrieved chunks don't support an answer).
- Every claim in the generated answer must be traceable to a specific retrieved
  chunk; the response includes which chunk(s) supported which part of the answer.
- If no retrieved chunk is a good enough match, the system says so explicitly
  rather than guessing.

### 2.5 Query Endpoint (PRD Story 6.5)

- New endpoint on the existing Cloud Run service (`budgetsense-app-v1`): `POST /query`
- Request: a natural-language question.
- Response: the generated answer, a list of citations (source document, page,
  authority tier), and enough detail to eyeball whether the answer is well-grounded.
- Same service account, same VPC connector, same Secret Manager pattern as the
  existing `/health` endpoint — no new identity or networking surface introduced.

## 3. Non-goals (this spec)

- No ReAct agent loop, no multi-step reasoning, no agent-initiated actions — this
  is a single-pass retrieve-then-generate flow. (The fuller agent vision is
  documented as reference-only in PRD §7 / architecture.md §9, not committed here.)
- No trust badge UI/scoring beyond returning authority tier and retrieval scores
  in the response — badge _design_ is out of scope, the underlying data isn't.
- No semantic cache (Memorystore/Redis) yet — can be added later if latency/cost
  become an issue; not required to prove the core RAG loop works.
- No frontend UI — `/query` is tested via curl/Postman, not a chat interface.

## 4. Acceptance Criteria

- [ ] At least 2–3 real budget policy PDFs ingested, parsed, and chunked.
- [ ] `pgvector` enabled on Cloud SQL; chunk embeddings stored and queryable.
- [ ] Hybrid search (vector + full-text, RRF-combined) returns sensible results
      for a test query where the correct answer is known in advance.
- [ ] `POST /query` returns a generated answer with citations for at least 3
      distinct test questions, verified by hand that the citations actually
      support the answer given.
- [ ] At least one test case where no good match exists, and the system says so
      rather than fabricating an answer.
- [ ] `specs/006-ai-layer/runbook.md` records the documents used, chunking
      approach, and the test questions with their actual results.

## 5. Files Introduced

```
specs/006-ai-layer/runbook.md
src/rag/                      # ingestion + retrieval + generation logic
src/main.py                   # extended with the new /query endpoint
```
