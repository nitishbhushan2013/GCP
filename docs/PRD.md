# Product Requirements Document (PRD): BudgetSense-GCP

## Document Control

| Field                            | Value                                                    |
| -------------------------------- | -------------------------------------------------------- |
| Status                           | Living document — updated as Epics complete              |
| Owner (Product)                  | Claude, acting as PO, on behalf of Nitish Bhushan        |
| Owner (Architecture)             | Claude, acting as Architect (see `docs/architecture.md`) |
| Source of truth for scope        | This document + `docs/project-brief.md`                  |
| Source of truth for build detail | `specs/NNN-*/spec.md` + matching `runbook.md` per Epic   |

---

## 1. Product Vision

A live, demoable, security-conscious GCP system that serves as verifiable, auditable
evidence of hands-on GCP capability.
The product is not the RAG feature alone; it is the **entire, defensible system**:
network, identity, workload, observability, governance, and AI, each built
deliberately and each explainable under technical questioning.

**Full end-state product vision** (the north star this project is building toward):

> BudgetSense is a full-stack AI platform that lets any user — citizen or government
> staff — ask a natural language question about the Federal Budget and receive a
> cited, source-verified answer in seconds, with the AI agent able to take real
> actions on their behalf. It is not a chatbot that guesses. It is not a search
> engine that returns links. It is an intelligent agent that:
>
> 1. Retrieves the most relevant, most authoritative source documents using a
>    custom RAG pipeline with hybrid search and authority-tier weighting
> 2. Answers with full citations, source URLs, and a trust badge indicating how
>    verified the answer is

Epic 6 (§4) currently scopes a simpler first slice of this vision (ingest → search
→ generate), and Epic 7 adds a public interface over that slice. The fuller
ReAct/agent-actions/trust-badge capability described above is the reference target
this project is oriented toward, not yet committed as Epic 6 or Epic 7 Stories —
see §7 for how the two relate.

## 2. Target "User"

| Persona              | Example question                                                                           |
| -------------------- | ------------------------------------------------------------------------------------------ |
| Property investor    | "I bought an investment property last year — am I affected by negative gearing changes?"   |
| Small business owner | "I run a café with $800K turnover. What Budget measures help my cash flow?"                |
| Family trust holder  | "Our family trust has run for 20 years. What changes and when do we need to act?"          |
| Salaried worker      | "I earn $95,000. How much better off will I be from all the tax cuts combined?"            |
| First home buyer     | "Does this Budget help or hurt us as first home buyers?"                                   |
| IT contractor        | "I operate through a company doing IT consulting. Does the Budget affect my structure?"    |
| Retiree              | "I'm retired on super. What does the Budget mean for me, especially if I travel overseas?" |

## 3. Epics & Stories

Status legend: ✅ Done · 🟡 Partial · ⬜ Backlog

---

### Epic 1: Network Foundation ✅ Done

**Goal:** A segmented, private-by-default network that everything else builds on.

| Story                                       | Acceptance Criteria                                                                   | Status | Evidence                                                   |
| ------------------------------------------- | ------------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------- |
| 1.1 Custom VPC with public/private subnets  | Custom-mode VPC, 2 subnets, both in `australia-southeast1`                            | ✅     | `specs/001-foundation/spec.md`, `runbook.md`               |
| 1.2 Cloud Run ↔ private subnet connectivity | Serverless VPC Access connector provisioned                                           | ✅     | same                                                       |
| 1.3 Cloud SQL private-IP path               | Private Services Access peering established                                           | ✅     | same                                                       |
| 1.4 Default-deny firewall posture           | No rule permits `0.0.0.0/0` on any admin port; explicit deny-all rule present         | ✅     | same                                                       |
| 1.5 IaC parity                              | Terraform imports and matches 100% of manually-built resources (`plan` shows no diff) | ✅     | `infra/terraform/`, ADR-001/002/003 in `docs/decisions.md` |

---

### Epic 2: Identity & Access Governance 🟡 Partial

**Goal:** Least-privilege identity is enforced everywhere workloads run, and every
privileged action is auditable.

| Story                                          | Acceptance Criteria                                                                                                              | Status          | Evidence                                               |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------- | ------------------------------------------------------ |
| 2.1 Dedicated service account for the workload | Cloud Run runs as a named SA, not the default Compute Engine SA                                                                  | ✅              | `specs/003-workload/runbook.md` (`budgetsense-run-sa`) |
| 2.2 Scoped Secret Manager access               | SA has `secretAccessor` on exactly the 4 secrets it needs — not project-wide                                                     | ✅              | same                                                   |
| 2.3 Scoped Cloud SQL access                    | SA has `roles/cloudsql.client`, nothing broader                                                                                  | ✅              | same                                                   |
| 2.4 Cloud Audit Logs enabled and reviewed      | Data Access audit logs confirmed enabled for the resources in this project; at least one log entry reviewed and explainable      | ⬜ Not yet done | —                                                      |
| 2.5 IAM least-privilege review                 | Full IAM bindings on the project reviewed for any over-broad grant (e.g. accidental Editor/Owner roles beyond the account owner) | ⬜ Not yet done | —                                                      |

_Note: Epic 2 was originally planned as its own phase (Spec 002) but its early
Stories were delivered opportunistically inside Epic 3's build rather than as a
standalone spec. Stories 2.4–2.5 remain open and should be completed as a proper
Spec 002 retrofit. Note also (Epic 7): Story 2.5's review should explicitly
confirm the `allUsers`/`run.invoker` binding added under ADR-008 is an
intentional, not accidental, grant — the review shouldn't flag it as a finding
without cross-referencing the ADR._

---

### Epic 3: Application Workload ✅ Done

**Goal:** A live, reachable service proving the private network path actually works
end-to-end, with no secrets in code or images.

| Story                              | Acceptance Criteria                                                                                | Status | Evidence                                                          |
| ---------------------------------- | -------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------- |
| 3.1 Private-IP Cloud SQL instance  | PostgreSQL, no public IP, dedicated app DB + non-superuser app user                                | ✅     | `specs/003-workload/runbook.md`                                   |
| 3.2 Credentials via Secret Manager | No credentials hardcoded or in deployed files; all 4 values sourced from Secret Manager at runtime | ✅     | same                                                              |
| 3.3 Containerized Python service   | Dockerfile, image built and pushed to Artifact Registry                                            | ✅     | `src/Dockerfile`, `src/main.py`                                   |
| 3.4 Cloud Run deployment           | Deployed with VPC connector, dedicated SA, min-instances=0                                         | ✅     | `specs/003-workload/runbook.md` (`budgetsense-app-v1`)            |
| 3.5 End-to-end health verification | `/health` returns a live DB round-trip, not just a TCP check                                       | ✅     | Verified response: `{"status":"healthy","db_connected":true,...}` |

**Known issues resolved during this Epic** (documented for interview value):

- Cloud Run's "Redeploy" does not re-resolve `latest` Secret Manager versions — a
  genuinely new revision is required.
- An invisible leading-space character in an env var name (`" DB_NAME"`) caused
  PostgreSQL to silently default the database name to the connecting username,
  producing a misleading error. Root-caused via `gcloud ... describe --format=yaml`
  rather than trusting the Console UI.

---

### Epic 4: Observability & Monitoring ✅ Done

**Goal:** The system's health and security posture are visible, not just assumed.

| Story                              | Acceptance Criteria                                                                                                    | Status |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------ |
| 4.1 Cloud Monitoring dashboard     | A dashboard showing Cloud Run request count/latency/error rate and Cloud SQL connection count                          | ✅     |
| 4.2 Log-based alert                | At least one alert policy (e.g. 5xx rate spike, or `/health` returning `unhealthy`) wired to a notification channel    | ✅     |
| 4.3 Security Command Center review | Findings reviewed at least once; any actionable finding triaged and either fixed or explicitly accepted with rationale | ✅     |

---

### Epic 5: Governance & Compliance ⬜ Backlog

**Goal:** Policy-level guarantees exist, not just individually-correct resource configs.

| Story                                  | Acceptance Criteria                                                                                                                                                                            | Status |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| 5.1 Data residency Organization Policy | Policy restricting resource location to Australian regions, applied and verified (attempt to create a resource outside `australia-southeast1`/`australia-southeast2` and confirm it's blocked) | ⬜     |
| 5.2 Public IP restriction policy       | Organization Policy blocking public IPs on Compute/Cloud SQL resources project-wide, not just by convention                                                                                    | ⬜     |

---

### Epic 6: Applied AI — RAG Layer 🟡 Partial

**Goal:** The actual "why this matters" feature — grounded, cited Q&A over budget
policy documents, mirroring BudgetSense's original AWS architecture on GCP-native
services.

| Story                   | Acceptance Criteria                                                                                                                  | Status |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------ |
| 6.1 Document ingestion  | Source budget policy documents stored in Cloud Storage                                                                               | ✅     |
| 6.2 Document parsing    | Document AI extracts text/structure from ingested documents                                                                          | ✅     |
| 6.3 Vector index        | Vector index built over parsed document chunks (via `pgvector`, ADR-004 deviation from the originally-named Vertex AI Vector Search) | ✅     |
| 6.4 Grounded generation | Gemini generates answers constrained to retrieved chunks, with citations back to source                                              | ✅     |
| 6.5 `/query` endpoint   | New Cloud Run endpoint accepting a question, returning a grounded, cited answer                                                      | ✅     |

_Note: all five Stories are functionally implemented and verified ad hoc against
real test questions (see `specs/006-ai-layer/development.md` Phases A–E). Epic
marked 🟡 Partial, not ✅ Done, because Phase F (formal verification against
spec.md's acceptance criteria, citation-accuracy spot-checks, and the runbook
write-up) has not yet been completed. Known limitations found during ad hoc
testing — table-chunking gaps, an imprecise "not found" distance threshold, and
one unconfirmed page-number metadata mismatch — are documented in
`docs/architecture.md` §6.3 and should be formally investigated or accepted in
Phase F._

---

### Epic 7: Web UI — Demo Interface 🟡 Partial

**Goal:** A polished, publicly and persistently reachable interface for the
`/query` endpoint that a technical reviewer can use directly, on their own
schedule — replacing curl/Postman as the demo method, and replacing any
requirement for a live session with the project owner.

**Scope note:** Epic 6's spec.md §3 listed "No frontend UI" as an explicit
non-goal for that spec specifically. This Epic is a deliberate, logged deviation
from that — the decision to build a UI is driven by demo/interview presentation
value, not a change to Epic 6's backend contract. `project-brief.md` §5 Phase 3
had, in fact, originally anticipated a frontend before Epic 3 deferred it in
favor of proving the backend first; Epic 7 fulfills that original intent now
that Epic 6 gives it something meaningful to call.

| Story                               | Acceptance Criteria                                                                                             | Status                                                           |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| 7.1 Static UI served                | A single HTML/CSS/JS page, served by the existing Cloud Run service (no new GCP resource, no new cost, ADR-007) | 🟡 Code written, not yet tested locally or deployed              |
| 7.2 Question input + submit         | Text input, submit button, loading state while awaiting the API response                                        | 🟡 Implemented in draft UI, pending verification                 |
| 7.3 Answer + citation display       | Renders the answer text and a distinct, styled citation list (doc, page, tier) per response                     | 🟡 Implemented in draft UI, pending verification                 |
| 7.4 Not-found state                 | A visually distinct state when `not_found: true`, rather than displaying it as a normal answer                  | 🟡 Implemented in draft UI, pending verification                 |
| 7.5 Error handling                  | Network/5xx failures show a clear message, not a blank or broken page                                           | 🟡 Implemented in draft UI, pending verification                 |
| 7.6 Public, persistent reachability | Anyone with the URL can use the UI at any time, without a live session or credential exchange (ADR-008)         | ✅ IAM binding confirmed live (`allUsers` / `roles/run.invoker`) |

---

## 5. Out of Scope (Product-level, not just Epic-level)

- Multi-tenant or multi-user auth — this is a single-reviewer-oriented demo product,
  though now publicly reachable by URL (ADR-008), not a real multi-tenant product
  with accounts or per-user data.
- SLA/uptime guarantees — acceptable to be cold-started (min-instances=0) for a
  portfolio project.
- Cost optimization beyond "genuinely $0 when idle" — no FinOps deep-dive planned.
  Note: Epic 7's public access (ADR-008) introduces a small, accepted risk of
  unexpected Gemini API cost from uncontrolled public usage; see ADR-008's
  revisit triggers.
- Abuse prevention (rate limiting, API keys) on the public UI — accepted as a
  future revisit trigger, not built now (ADR-008).

## 6. Open Product Decisions

- Epic 2 (Identity) needs a proper retrofit spec (Spec 002) to close Stories 2.4–2.5
  before this Epic can be marked Done — currently the weakest-documented part of the
  system despite being partially implemented.
- Epic 6's Phase F (formal verification, runbook) should be completed before
  Epic 6 is marked fully Done.
- Epic 7's Stories 7.1–7.5 need local browser testing, then a Docker rebuild
  (`:v3`) and production deployment + verification before being marked Done.
- Decide whether Epic 5 (Governance) or completing Epic 6/7's open items should
  be prioritized next.

## 7. Extended Vision — Reference Only, Not Committed Scope

This section captures the full product ambition for context. **Epic 6's Stories
(§3) and Epic 7's Stories remain the committed, buildable scope** — this section
is not a backlog, it's the "why" behind Epic 6/7 and a preview of what they could
grow into later.

The full vision adds three capabilities beyond current scope:

- A **ReAct agent loop** (retrieve → reason → possibly retrieve again → act →
  answer) rather than a single-pass retrieve-then-generate flow
- **Agent actions** — the system doing something on the user's behalf (e.g.
  generating a personalized document), not just answering
- A **trust badge** — a computed confidence/verification signal shown alongside
  every answer, not just a citation list

If/when this becomes committed scope, it should be written up as new Stories
(or a new Epic 8) with proper acceptance criteria — deliberately not done here,
to keep this section descriptive rather than prescriptive.

### Epic 8: Multi-Hop Agentic Retrieval (ReAct) ⬜ Backlog

**Goal:** Answer compound, multi-topic citizen questions correctly — the kind
PRD §2's own personas actually ask (a trust holder asking what changes AND
when to act; a family asking about combined tax relief) — by reasoning about
what's actually being asked, retrieving for each distinct need separately,
and synthesizing one grounded answer, rather than forcing one embedding to
represent several topics at once.

**Scope note:** This formally retires Epic 6 `spec.md` §3's non-goal "no
ReAct agent loop, no multi-step reasoning" and promotes §7's "Extended
Vision" ReAct capability from reference-only to committed scope. Driven by
a real, observed failure: a compound question ("what changes for our
20-year discretionary trust, and when do we act") produced weak retrieval
(vector distance ~0.42-0.46, roughly double a clean single-topic match) and
a correct-but-unhelpful "not found" response — a single embedding of a
multi-topic question represents none of its topics well (see ADR-010).

| Story                                | Acceptance Criteria                                                                                                                                       | Status |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| 8.1 Question decomposition           | A compound question is broken into 1-4 focused, factual (never advice-framed) sub-questions                                                               | ⬜     |
| 8.2 Multi-hop retrieval              | Each sub-question runs through the existing Phase C retrieval pipeline independently; results deduped by section                                          | ⬜     |
| 8.3 Sufficiency check & re-query     | If gathered context doesn't cover the question, the agent generates and retrieves one additional targeted sub-question, bounded to prevent infinite loops | ⬜     |
| 8.4 Synthesized generation           | One answer synthesized across all gathered sections, with citations spanning multiple sub-questions' sources                                              | ⬜     |
| 8.5 No regression on single-topic Qs | The original 5 single-fact test questions still resolve in effectively one hop, same quality as before                                                    | ⬜     |
| 8.6 Endpoint parity                  | `/query`'s external contract (`answer`, `citations`, `not_found`) is unchanged — this is an internal upgrade                                              | ⬜     |

### Story 8.3: Sufficiency check with bounded one-retry gap-fill — Done

After multi-hop retrieval, an LLM-based sufficiency check judges whether the
retrieved sections plausibly cover the original question. If not, it writes
one targeted gap-question and retrieval runs exactly once more against it —
never a loop. Tested against WATO (single-topic, sufficient on first pass),
the discretionary trust question (initial pass missed the trust explainer
document entirely; retry correctly recovered it), a broad tax-planning
question (flagged insufficient; retry found no new sections — accepted
limitation, logged in architecture.md §6.5), and a Mars colonization
negative control (correctly flagged insufficient; refusal is generation's
responsibility, not retrieval's — see §6.5 note).
