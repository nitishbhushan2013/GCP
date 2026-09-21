# Spec 008: Multi-Hop Agentic Retrieval (ReAct)

## Status

Draft → Implementing (Phase A done)

## 1. Problem

Epic 6's single-pass RAG (embed question → hybrid retrieve → generate) works well
for single-fact questions, but fails on compound, multi-topic questions — exactly
the kind PRD §2's own personas actually ask (a trust holder asking what changes AND
when to act; a family asking about combined tax relief for working parents).

Observed directly during Epic 7 testing: a compound question ("our family has run a
discretionary trust for 20 years, what changes and when do we act") produced weak
retrieval (vector distance ~0.42–0.46, roughly double a clean single-topic match at
~0.21) and a correct-but-unhelpful "not found" response. A single embedding of a
multi-topic question represents none of its topics well — this is a structural
limit of single-pass RAG on compound input, not something a higher `top_k` fixes
(more results ranked by the same diluted vector is not more signal). See ADR-010.

This formally retires Epic 6 `spec.md` §3's non-goal "no ReAct agent loop, no
multi-step reasoning" and promotes architecture.md §9's "Extended Vision" ReAct
capability from reference-only to committed scope.

## 2. Requirements

### 2.1 Question Decomposition (PRD Story 8.1)

- A new `decompose_question()` function (`src/rag/agent.py`) breaks a citizen
  question into 1–4 focused sub-questions.
- Each sub-question must be self-contained — answerable independently, without
  needing another sub-question's answer first.
- Each sub-question must be purely factual (what a policy/rate/threshold/date/
  eligibility rule _is_), never advice-framed (what the citizen _should do_).
  Advice-seeking language ("best way to", "how can I reduce", "what should I do")
  gets reworded into a request for the underlying facts.
- A single-topic question is not split — it comes back as one sub-question, the
  original question unchanged (only reworded if advice-framed).
- Implemented via a Vertex AI Gemini call (`gemini-2.5-flash`, `temperature=0.0`,
  JSON response mode) — deterministic, structured output, no regex scraping needed.

### 2.2 Multi-Hop Retrieval (PRD Story 8.2)

- Each sub-question is run through the existing Phase C `retrieve()` pipeline
  independently (vector + full-text + RRF + authority boost + parent lookup) —
  reused unchanged, not modified.
- Results across all sub-questions are deduplicated by `section_id` before
  reaching generation, so a section relevant to two sub-questions isn't sent to
  Gemini twice.

### 2.3 Sufficiency Check & Bounded Re-query (PRD Story 8.3)

- After the initial retrieval pass, the agent checks whether the gathered
  parent sections plausibly cover the original question.
- If not, it generates and retrieves exactly **one** additional targeted
  sub-question to fill the gap — bounded to a single retry, never an open loop.

### 2.4 Synthesized Generation (PRD Story 8.4)

- One Gemini call synthesizes a single answer across all gathered parent
  sections (initial + any gap-filling retry), extending Phase D's
  `generate_answer` prompt pattern rather than replacing it.
- Citations in the synthesized answer can span sources gathered from different
  sub-questions.

### 2.5 No Regression on Single-Topic Questions (PRD Story 8.5)

- The original 5 single-fact test questions from Epic 6 must still resolve in
  effectively one retrieval hop, at the same answer quality as before Epic 8.

### 2.6 Endpoint Parity (PRD Story 8.6)

- `POST /query`'s external response contract (`answer`, `citations`,
  `not_found`) is unchanged. Epic 8 is an internal upgrade to what happens
  between request and response, not a new endpoint or a breaking schema change.

## 3. Non-goals (this spec)

- No new Cloud Run endpoint, no request/response schema changes (Story 8.6).
- No unbounded agent loop — the sufficiency re-query is capped at exactly one
  extra retrieval pass (see ADR-010's tradeoff note on latency/cost).
- No changes to Phase C's `retrieve()` internals (vector search, full-text
  search, RRF fusion, authority boost) — Epic 8 wraps it, doesn't modify it.
- No UI changes — Epic 7's frontend is unaffected; it already just renders
  whatever `/query` returns.
- No formal evaluation harness/benchmark suite beyond the existing hand-run
  test questions (5 single-topic from Epic 6 + the compound questions used to
  motivate and verify Epic 8).

## 4. Acceptance Criteria

- [x] `decompose_question()` splits a compound question into 1–4 focused,
      factual, non-advice-framed sub-questions; a single-topic question stays
      as one sub-question. Verified standalone against 3 test questions (WATO,
      discretionary trust, tax planning) — see `development.md` Phase A.
- [x] Each sub-question independently runs through the existing `retrieve()`
      pipeline; results deduplicated by `section_id`.
- [ ] When gathered context is insufficient, exactly one bounded gap-filling
      sub-question is generated and retrieved — never more than one retry.
- [ ] A single synthesis call produces one answer with citations spanning
      multiple sub-questions' sources.
- [ ] The original 5 single-fact Epic 6 test questions still resolve in
      effectively one hop, same quality as before.
- [ ] `POST /query`'s response contract (`answer`, `citations`, `not_found`)
      is unchanged end-to-end.
- [ ] `specs/008-agentic-retrieval/development.md` records the working
      checklist and actual findings at each phase.

## 5. Files Introduced

\```
specs/008-agentic-retrieval/development.md
src/rag/agent.py # decompose_question(), sufficiency check, gap re-query, synthesis wiring
src/rag/test_decompose.py # standalone decomposition test (no DB required)
src/main.py # /query updated internally to call the Epic 8 agent flow
\```
