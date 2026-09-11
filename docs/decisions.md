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
