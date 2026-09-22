# Development Sequence: Spec 008 — Multi-Hop Agentic Retrieval

This is the working checklist for building Epic 8, in strict execution order. Update
the status marker as each step completes. This is a living document during active
development — once the Epic is done, its findings get folded into
`specs/008-agentic-retrieval/runbook.md` as the permanent record.

Status legend: ⬜ Not started · 🔄 In progress · ✅ Done

## Phase A — Question Decomposition (code)

- [✅] A1. Write `decompose_question()` in `src/rag/agent.py` — Vertex AI `genai`
  client, `gemini-2.5-flash`, `temperature=0.0`, `response_mime_type="application/json"`
- [✅] A2. Prompt enforces: 1–4 sub-questions, self-contained, purely factual
  (never advice-framed), no split on single-topic questions, no invented topics
- [✅] A3. Fallback: malformed/empty JSON from Gemini returns `[question]`
  unchanged rather than reaching retrieval with nothing
- [✅] A4. Write standalone test harness `src/rag/test_decompose.py` (no DB
  required — decomposition doesn't touch retrieval)
- [✅] A5. Run against 3 test questions and confirm behaviour: - WATO (single-topic) → stayed as 1 sub-question - Discretionary trust (compound) → decomposed into 2 factual sub-questions - Tax planning (compound, advice-framed) → decomposed into 3 factual
  sub-questions, "best way to reduce my tax" successfully reworded away
  from advice framing
- [✅] A6. Note for later phases: the tax-planning decomposition added a
  superannuation-contributions sub-question not literally present in the
  original question — a reasonable inference, but scope the model
  introduced on its own. Watch this in Phase D synthesis and revisit the
  prompt's "don't invent topics" rule if it causes noisy answers.

## Phase B — Multi-Hop Retrieval Wiring (code)

- [✅] B1. Write a loop that runs each decomposed sub-question through the
  existing `retrieve()` pipeline (Phase C of Epic 6) independently
- [✅] B2. Collect parent sections across all sub-questions
- [✅] B3. Dedupe collected parent sections by `section_id`
- [✅] B4. Manually test against the discretionary trust and tax-planning
  questions — confirm retrieval now returns sections for _each_ sub-topic,
  not one diluted set

## Phase C — Sufficiency Check & Bounded Re-query (code)

- [✅] C1. Define what "sufficient" means (e.g. every sub-question has at least
  one parent section above a distance/rank threshold)
- [✅] C2. If insufficient, generate exactly one gap-filling sub-question
  (Gemini call) targeting the uncovered part of the question
- [✅] C3. Retrieve for the gap sub-question and merge into the deduped set
  (Phase B3's dedupe applies again)
- [✅] C4. Hard-cap at one retry — confirm there is no path to a second
  gap-query even if the first retry is also insufficient

## Phase D — Synthesized Generation (code)

- [⬜] D1. Extend Phase D's `generate_answer` prompt pattern to accept parent
  sections gathered from multiple sub-questions
- [⬜] D2. Confirm citation parsing (`parse_response`) still correctly maps
  `[Source N, p.X]` back to the right document when sources came from
  different sub-questions
- [⬜] D3. Manually verify the synthesized answer for the trust and
  tax-planning questions is not just "unhelpful, not found" as before

## Phase E — Endpoint Wiring & Regression Check

- [⬜] E1. Wire `src/main.py`'s `/query` endpoint to call the Epic 8 agent flow
  (decompose → multi-hop retrieve → sufficiency check → synthesize)
  instead of Epic 6's single-pass flow
- [⬜] E2. Confirm `/query`'s request/response shape is unchanged (Story 8.6)
- [⬜] E3. Re-run the original 5 Epic 6 single-fact test questions against the
  updated endpoint — confirm they still resolve in effectively one hop,
  same answer quality as before (Story 8.5)

## Phase F — Verification (per Spec 008 acceptance criteria)

- [⬜] F1. Run the discretionary trust and tax-planning questions against the
  live `/query` endpoint end-to-end
- [⬜] F2. Verify each citation in the synthesized answer actually supports its
  claim (manual check against source PDF text)
- [⬜] F3. Confirm the 5 Epic 6 regression questions still pass (Story 8.5)
- [⬜] F4. Write `specs/008-agentic-retrieval/runbook.md` with final results,
  the sufficiency-check logic used, and actual test outputs

## Phase G — Documentation & Cleanup

- [🔄] G1. Log ADR-010: multi-hop ReAct-style retrieval over single-pass RAG — done
- [✅] G2. Update `docs/PRD.md` Story 8.1 to ✅ Done, Epic 8 status Backlog → Partial
- [✅] G3. Update `docs/architecture.md` §6.5 with Phase A status note
- [⬜] G4. Update `docs/PRD.md` Stories 8.2–8.6 as each phase completes
- [⬜] G5. Write the short Epic 8 takeaways + interview pitch doc (per the
  standing preference)

---

**Phase A complete. Where we are right now: Phase B, step B1** — write the multi-hop retrieval loop over the existing `retrieve()` pipeline.
