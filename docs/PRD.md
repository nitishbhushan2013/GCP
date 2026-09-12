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

A live, demoable, security-conscious GCP system — a rebuild of BudgetSense (hybrid
RAG over Australian Federal Budget policy) — that serves as verifiable, auditable
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
> 2. Reasons across multiple sources using a ReAct agent loop
> 3. Answers with full citations, source URLs, and a trust badge indicating how
>    verified the answer is

Epic 6 (§4) currently scopes a simpler first slice of this vision (ingest → search
→ generate). The fuller ReAct/agent-actions/trust-badge capability described above
is the reference target this project is oriented toward, not yet committed as Epic
6 Stories — see §7 for how the two relate.

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
Spec 002 retrofit._

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
| 4.1 Cloud Monitoring dashboard     | A dashboard showing Cloud Run request count/latency/error rate and Cloud SQL connection count                          | ⬜     |
| 4.2 Log-based alert                | At least one alert policy (e.g. 5xx rate spike, or `/health` returning `unhealthy`) wired to a notification channel    | ⬜     |
| 4.3 Security Command Center review | Findings reviewed at least once; any actionable finding triaged and either fixed or explicitly accepted with rationale | ⬜     |

---

### Epic 5: Governance & Compliance ⬜ Backlog

**Goal:** Policy-level guarantees exist, not just individually-correct resource configs.

| Story                                  | Acceptance Criteria                                                                                                                                                                            | Status |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| 5.1 Data residency Organization Policy | Policy restricting resource location to Australian regions, applied and verified (attempt to create a resource outside `australia-southeast1`/`australia-southeast2` and confirm it's blocked) | ⬜     |
| 5.2 Public IP restriction policy       | Organization Policy blocking public IPs on Compute/Cloud SQL resources project-wide, not just by convention                                                                                    | ⬜     |

---

### Epic 6: Applied AI — RAG Layer ⬜ Backlog

**Goal:** The actual "why this matters" feature — grounded, cited Q&A over budget
policy documents, mirroring BudgetSense's original AWS architecture on GCP-native
services.

| Story                   | Acceptance Criteria                                                                     | Status |
| ----------------------- | --------------------------------------------------------------------------------------- | ------ |
| 6.1 Document ingestion  | Source budget policy documents stored in Cloud Storage                                  | ⬜     |
| 6.2 Document parsing    | Document AI extracts text/structure from ingested documents                             | ⬜     |
| 6.3 Vector index        | Vertex AI vector search index built over parsed document chunks                         | ⬜     |
| 6.4 Grounded generation | Gemini generates answers constrained to retrieved chunks, with citations back to source | ⬜     |
| 6.5 `/query` endpoint   | New Cloud Run endpoint accepting a question, returning a grounded, cited answer         | ⬜     |

---

## 5. Out of Scope (Product-level, not just Epic-level)

- Multi-tenant or multi-user auth — this is a single-reviewer demo product, not a
  real user-facing product.
- SLA/uptime guarantees — acceptable to be cold-started (min-instances=0) for a
  portfolio project.
- Cost optimization beyond "genuinely $0 when idle" — no FinOps deep-dive planned.

## 6. Open Product Decisions

- Epic 2 (Identity) needs a proper retrofit spec (Spec 002) to close Stories 2.4–2.5
  before this Epic can be marked Done — currently the weakest-documented part of the
  system despite being partially implemented.
- Decide whether Epic 4 (Monitoring) or Epic 6 (AI Layer) should be built next —
  Epic 6 is the higher-impact "wow" feature, but Epic 4 is smaller and closes out
  the original 5-phase plan in order. Recommend discussing before starting either.

## 7. Extended Vision — Reference Only, Not Committed Scope

This section captures the full product ambition for context. **Epic 6's Stories
(§4) remain the committed, buildable scope** — this section is not a backlog, it's
the "why" behind Epic 6 and a preview of what Epic 6 could grow into later.

The full vision adds three capabilities beyond Epic 6's current scope:

- A **ReAct agent loop** (retrieve → reason → possibly retrieve again → act →
  answer) rather than a single-pass retrieve-then-generate flow
- **Agent actions** — the system doing something on the user's behalf (e.g.
  generating a personalized document), not just answering
- A **trust badge** — a computed confidence/verification signal shown alongside
  every answer, not just a citation list

If/when this becomes committed scope, it should be written up as new Epic 6
Stories (or a new Epic 7) with proper acceptance criteria — deliberately not done
here, to keep this section descriptive rather than prescriptive.
