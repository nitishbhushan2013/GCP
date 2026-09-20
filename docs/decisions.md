# Architecture Decisions

A running log of notable design decisions and their tradeoffs, in the order they were made.

## ADR-001: Manual console build before Terraform

**Date:** Spec 001 (Foundation)
**Decision:** Build Phase 1 (VPC, subnets, firewall) by hand in the GCP Console rather
than starting with Terraform.
**Why:** The goal of this project is to demonstrate genuine, hands-on GCP understanding
— clicking through the actual Console builds an intuition for what each setting does
that copy-pasting a Terraform module doesn't. Terraform can always be layered on
afterward once the manual build is understood and verified working.
**Tradeoff:** No IaC reproducibility yet for Phase 1; the environment is manually
built and not easily torn down/recreated. Acceptable for a portfolio project; would
not be acceptable for a production team environment.
**Revisit if:** the environment needs to be reproducible (e.g. for a demo reset, or to
show IaC skill explicitly) — tracked as a potential Phase 1b spec.

## ADR-002: Cloud Run over GKE for the workload phase

**Date:** Between Spec 001 and Spec 003 (Workload)
**Decision:** Use Cloud Run for the application workload, not GKE (Standard or
Autopilot).
**Why:** This is a zero-budget demo project. GKE — in any mode, zonal or regional —
carries a flat $0.10/hour cluster management fee (covered by Google's $74.40/month
free credit only for a single zonal or Autopilot cluster) plus continuous node compute
cost while the node pool is non-zero. Cloud Run has no cluster fee at all and bills
per-request, scaling genuinely to zero with no idle cost and nothing to remember to
tear down between sessions.
**Tradeoff:** Loses the opportunity to demonstrate hands-on Kubernetes/node-pool
management in this project. Docker/Artifact Registry usage is still retained (Cloud
Run runs container images pulled from Artifact Registry), so containerization
knowledge is still demonstrated — just not orchestration at the Kubernetes level.
**Revisit if:** cost is no longer a constraint, or a specific interview signals GKE
experience is a hard requirement.

## ADR-003: Untagged (broadly-applied) firewall rules, including SSH

**Date:** Phase 1b (Terraform reconciliation)
**Decision:** Remove `target_tags` from all four firewall rules, including
`allow-iap-ssh`, so they apply to every instance in the VPC rather than requiring
an opt-in network tag.
**Why:** Tag-based scoping introduces a human-error risk: any resource created
without the matching tag silently loses connectivity (internal traffic, health
checks) or, worse, silently gains no SSH path when one was expected — for a
solo-maintained portfolio project, consistency and simplicity were prioritized
over the extra scoping.
**Tradeoff:** `allow-iap-ssh` losing its tag is the meaningful one — it means any
instance in the VPC becomes SSH-reachable via Identity-Aware Proxy without needing
individual opt-in. This is a real widening of blast radius versus the original
design (see ADR/spec history). Mitigated by: IAP still requires an explicit IAM
grant to actually establish a connection, and no compute instances exist in this
project yet, so current exposure is zero.
**Revisit if:** a bastion/jump host or any SSH-accessible VM is introduced —
at that point, re-scoping this rule to a tag (or better, to specific instance
names) should be reconsidered as the project matures past "solo demo."

## ADR-004: Cloud SQL + pgvector over Vertex AI Vector Search

**Date:** Epic 6 (AI Layer)
**Decision:** Implement vector search using the `pgvector` extension on the existing
Cloud SQL PostgreSQL instance, rather than deploying a Vertex AI Vector Search index.
**Why:** Vertex AI Vector Search requires a continuously-deployed index endpoint
that bills hourly regardless of query volume — the same category of always-on cost
problem GKE presented (see ADR-002). `pgvector` on the existing, already-provisioned
Cloud SQL instance adds vector search with zero additional idle cost, and combined
with Postgres's native full-text search enables the same BM25 + dense vector hybrid
approach used in BudgetSense's original AWS design (Aurora + pgvector) — a closer
architectural match than Vertex AI Vector Search would have been anyway.
**Tradeoff:** PRD Story 6.3 was originally written naming "Vertex AI vector search
index" specifically. This is a deliberate deviation from that literal wording,
made for cost reasons; the Story's underlying intent (a working vector index over
document chunks) is still met. Also: `pgvector` on a small Cloud SQL tier won't
scale to the size/performance a dedicated Vertex AI Vector Search deployment could
handle — acceptable for a portfolio-scale document set, would need revisiting at
real production scale.
**Revisit if:** the document corpus grows large enough that `pgvector` performance
on a small Cloud SQL instance becomes a genuine bottleneck.

## ADR-005: Hierarchical (parent-child) chunking over flat chunking

**Date:** Epic 6 (AI Layer), before ingestion pipeline built
**Decision:** Store two levels per document: small "child" chunks (~150-250 tokens)
that get embedded and searched, and larger "parent" sections (~1,500-2,500 tokens)
that are stored as plain text and retrieved for generation once a child chunk
matches.
**Why:** Flat chunking forces a tradeoff that hurts one side no matter which way
you tune it: small chunks match precisely but often lack enough surrounding
context for Gemini to generate a complete, well-grounded answer; large chunks
generate well but match imprecisely, since the embedding represents several
unrelated ideas at once. Hierarchical chunking gets both: precise matching via
small chunks, complete context via their parent section.
**Tradeoff:** More complex schema (two tables instead of one) and an extra lookup
per retrieval (child match \u2192 parent fetch). Considered acceptable given the
schema change costs nothing at this stage (built before any data was ingested).
**Revisit if:** the extra join/lookup becomes a measurable latency problem at a
scale this project isn't expected to reach.

## ADR-006: Document AI Processor Region Exception

**Status:** Accepted
**Date:** 2026-09-13
**Context:** Epic 6 — AI Layer

### Decision

The Document AI OCR processor (`budgetsense-ocr`, ID `1bd3e26847822f34`) was created
in region `us` rather than `australia-southeast1`.

### Context

The project's default data-residency posture (established in Epic 5 governance work)
restricts resources to Australian regions. Document AI's OCR processor type is not
available in `australia-southeast1` at time of writing — only a subset of regions
(`us`, `eu`) support it for this processor type.

### Options considered

1. **Use `us` region for this processor only** — accepted
2. Skip Document AI entirely, use a different OCR/parsing approach that runs in-region
3. Wait for Google to add `australia-southeast1` support

### Rationale

This is a portfolio/demo project processing publicly available Federal Budget PDFs —
not sensitive or classified data — so a regional exception carries no real compliance
risk here. Options 2 and 3 would have added significant complexity or blocked progress
for no material benefit. The exception is scoped narrowly: only the Document AI
processor sits outside `australia-southeast1`; all other resources (Cloud Storage,
Cloud SQL, Cloud Run) remain in-region.

### Consequences

- This deviation is called out explicitly rather than left implicit, so it can be
  defended in review (e.g. "why isn't everything in-region?").
- In a real production/Defence context, this would require either an approved
  exception process or a different OCR solution — noted here as the real-world
  caveat to this decision.

### Related

- ADR-005 (hierarchical chunking) — same epic, same ingestion pipeline

## ADR-007: Serve the demo UI from Cloud Run, not a separate GCS static site

**Date:** Epic 7 (Web UI)
**Decision:** Serve the UI as static files mounted directly on the existing
`budgetsense-app-v1` Cloud Run service, rather than provisioning a separate
Cloud Storage static website bucket.
**Why:** Zero new cost, zero new IAM surface, zero new resource to explain or
secure — consistent with this project's cost and least-privilege goals
(architecture.md §1). A second hosting mechanism would also mean two deploy
paths and two places CORS/access could go wrong, for a purely cosmetic
UI addition. Same-origin serving (UI and API on the same domain) also means
no CORS configuration is needed at all.
**Tradeoff:** Doesn't demonstrate GCS static hosting as a distinct GCP skill.
Considered acceptable since Epic 1-6 already demonstrate substantially more
GCP breadth (VPC, IAM, Cloud SQL, Document AI, Vertex AI, Monitoring) than
one more storage pattern would add.
**Revisit if:** the UI needs to scale independently of the API, or a specific
interview signals GCS/CDN static-hosting experience is a hard requirement.

## ADR-008: Public unauthenticated access to the Cloud Run service

**Date:** Epic 7 (Web UI)
**Decision:** Grant `allUsers` the `roles/run.invoker` role on `budgetsense-app-v1`,
allowing anyone with the URL to use the UI and `/query` endpoint without
authentication, at any time — not just during a live, supervised demo session.
**Why:** The point of Epic 7's UI is to let a reviewer explore the system on
their own schedule, not only when the project owner is present to grant
access or share a token. A private, IAM-gated Cloud Run service would defeat
that purpose — a reviewer with a URL but no invoker permission just sees a 403.
**Verified:** `gcloud run services get-iam-policy` initially showed an empty
policy (no explicit bindings), despite the service already being reachable
without auth — indicating public access was originally granted via the
`--allow-unauthenticated` deploy-time flag rather than an explicit IAM
binding. Added `allUsers`/`roles/run.invoker` explicitly so the grant is
visible directly in the IAM policy, not just inferred from deploy history.
**Tradeoff:** This is a direct, acknowledged trade against this project's own
architectural goal #3 (least privilege by default — architecture.md §1). Two
real consequences: (1) anyone who obtains the URL can query it, including
triggering billed Gemini API calls, not just Cloud Run's own compute; (2) no
usage attribution — a log entry doesn't distinguish a genuine reviewer from
anyone else who found the link.
**Mitigations considered, not implemented:** Cloud Armor rate limiting, or a
lightweight shared token, would reduce abuse risk but add infrastructure and
complexity disproportionate to a single-reviewer-facing portfolio demo (see
project-brief.md §6, "cost optimization pass" already out of scope). Accepted
as-is for now.
**Revisit if:** the URL is shared broadly beyond intended reviewers, or
unexpected Gemini API cost appears in billing — at that point, a Cloud Armor
rate-limit rule or an API key check on `/query` would be the first fix to add.
**Related:** Data itself carries low risk regardless of access — all ingested
documents (Budget Papers) are already public Australian Government
publications, not sensitive or classified data (same reasoning as ADR-006's
data-residency exception).

## ADR-009: Dedicated public bucket for source PDFs, separate from the ingestion bucket

**Date:** Epic 7 (Web UI)
**Decision:** Create a new bucket, `budgetsense-gcp-prod-docs-public`, holding
copies of source Budget PDFs with `allUsers`/`roles/storage.objectViewer`
granted at the bucket level. The original ingestion bucket
(`budgetsense-gcp-prod-docs`) remains private and unchanged.
**Why:** Citations are only meaningfully verifiable if a reviewer can click
through to the actual source page — that's the entire point of building a
citation system in the first place. The existing docs bucket has uniform
bucket-level access enabled (ADR from Phase B's A3 fix), so IAM can only be
granted bucket-wide, not per-object; making that bucket public would also
expose `docai-output/` (Document AI's parsed JSON), which is harmless data
but unnecessary exposure. A separate, purpose-built public bucket keeps the
exposure scoped to exactly the 3 files that need it.
**Tradeoff:** A second bucket to maintain, and any future re-ingestion (a
new PDF added, or the existing 3 re-processed) now needs a corresponding
copy step into the public bucket, or citations for it will 404. Considered
acceptable given the copy is a single `gcloud storage cp` command, not a
recurring burden at this project's scale.
**Data risk:** Minimal — these are already-public Australian Government
Budget Paper publications (same reasoning as ADR-006), not sensitive or
classified data.
**Related risk:** the citation's `#page=N` fragment links directly to a
PDF page number sourced from stored `page_number` metadata. Phase D's
testing found one confirmed instance where that stored value didn't match
the PDF's own printed page label (ADR/finding noted in architecture.md
§6.3). This was a background data-quality note when citations were
plain text; it becomes a user-facing risk now that citations are clickable
links — a wrong page number sends a reviewer to the wrong page. Deferred
to Phase F investigation as already planned, but its priority increases
now that citations link out.
**Revisit if:** more source documents are added regularly enough that the
manual copy step becomes a real burden — at that point, wiring an
automatic copy into the Phase B ingestion script would be worth doing.

## ADR-010: Multi-hop ReAct-style retrieval over single-pass RAG

**Date:** Epic 8
**Decision:** Replace `/query`'s single embed→retrieve→generate pass with a
bounded reasoning loop: decompose the question into factual sub-questions,
retrieve independently per sub-question, check sufficiency, optionally
retrieve once more for a gap, then synthesize one answer across everything
gathered.
**Why:** A single embedding cannot represent a multi-topic question well —
observed directly: a compound trust/family question produced vector
distances of 0.42-0.46, roughly double a clean single-topic match (~0.21),
and a correct-but-unhelpful refusal rather than a wrong answer. This is a
structural limitation of single-pass RAG on compound input, not fixable by
raising top_k (more results ranked by the same diluted vector is not more
signal).
**Tradeoff:** Real cost and latency increase — a compound question now
costs 1 decomposition call + N retrieval passes + up to 1 re-query + 1
synthesis call, versus 1 retrieval + 1 generation call before. A simple
question ("WATO amount") should still resolve in effectively one hop
(PRD Story 8.5), so the cost increase should be concentrated on genuinely
compound questions, not uniform across all traffic.
**Revisit if:** latency becomes unacceptable for the demo UI's loading-state
expectations, or Gemini API cost from repeated calls per question becomes
material (relevant given ADR-008's public, unauthenticated access — more
reason to bound iteration count strictly).
**Related:** PRD Epic 8, retires Epic 6 spec.md §3's ReAct non-goal.
