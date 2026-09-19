# Spec 007: Web UI — Demo Interface

## Status

Draft

## 1. Problem

Epic 6 delivered a working `/query` API, but demoing it via curl/Postman
undersells the work. This spec adds a single-page UI, served with
zero new infrastructure (ADR-007).

## 2. Requirements

### 2.1 Static Serving (PRD Story 7.1)

- FastAPI `StaticFiles` mount serves a `static/` directory from the existing
  Cloud Run service.
- No new GCP resources, no new Docker image complexity beyond copying one
  more directory.

### 2.2 Question Input (PRD Story 7.2)

- Single text input + submit button.
- Visible loading state while the `/query` request is in flight (a Gemini
  call is not instant — an unresponsive-looking page during a 2-5 second
  wait reads as broken, not slow).

### 2.3 Answer + Citations (PRD Story 7.3)

- Answer text rendered clearly, separated visually from citations.
- Each citation shows source document, page, and authority tier as a
  distinct, styled element (not a raw JSON dump).

### 2.4 Not-Found State (PRD Story 7.4)

- When `not_found: true` in the response, render a visually distinct
  "no answer found" state — reinforces the grounding story (Phase D) as a
  visible, demoable feature, not just a backend behavior.

### 2.5 Error Handling (PRD Story 7.5)

- Network failure or non-2xx response shows a clear, styled error message.

## 3. Non-goals

- No build tooling (webpack/vite/npm) — single self-contained HTML file with
  inline CSS/JS, consistent with this project's zero-idle-cost, low-complexity
  ethos.
- No routing/multi-page app — one page, one interaction.
- No auth, no session/history persistence (matches PRD §5's existing
  single-reviewer-demo scoping).

## 4. Acceptance Criteria

- [ ] UI loads at the Cloud Run root URL with no separate deployment step.
- [ ] Submitting a real question displays a correct answer with citations
      within a reasonable wait, with a visible loading state throughout.
- [ ] Submitting the Mars negative-control question displays the not-found
      state distinctly, not as a generic answer box.
- [ ] Killing the network mid-request (or hitting a malformed response)
      shows an error state, not a silent failure or blank screen.

## 5. Files Introduced

```
src/static/index.html    # single self-contained page: HTML + CSS + JS
src/main.py              # extended with a StaticFiles mount
```
