# Architecture Document: BudgetSense-GCP

## Document Control

| Field               | Value                                                                                             |
| ------------------- | ------------------------------------------------------------------------------------------------- |
| Status              | Living document — updated as Epics complete                                                       |
| Owner               | Claude, acting as Architect, on behalf of Nitish Bhushan                                          |
| Companion documents | `docs/PRD.md` (what/why), `docs/decisions.md` (individual ADRs), `specs/NNN-*/` (per-Epic detail) |

This document is the **consolidated "how"** — it doesn't replace individual specs or
ADRs, it ties them together into one coherent system view.

---

## 1. Architectural Goals

Ranked, since they occasionally trade off against each other:

1. **Explainability** — every component must be defensible under questioning, not
   just functional.
2. **Zero idle cost** — this is a demo project, not production; nothing should bill
   while not actively being used.
3. **Least privilege by default** — identity, network, and secrets access are all
   scoped as narrowly as the system allows.
4. **Data residency** — everything lives in Australian GCP regions.
5. **Reproducibility** — Terraform manages the foundation; manual-console-first is a
   _learning_ choice, not a permanent one (see ADR-001).

Where goals conflict (e.g. Epic 1's untagged firewall rules trade some blast-radius
control for operational simplicity — ADR-003), the tradeoff is documented, not hidden.

---

## 2. System Context

```mermaid
graph TB
    Reviewer["Technical Reviewer<br/>(interview demo)"]
    Internet["Public Internet"]
    CloudRun["Cloud Run<br/>budgetsense-app-v1<br/>(Python/FastAPI)"]
    CloudSQL["Cloud SQL<br/>PostgreSQL<br/>(private IP only)"]
    SecretMgr["Secret Manager<br/>(4 scoped secrets)"]
    ArtifactReg["Artifact Registry<br/>(Docker images)"]
    VPC["VPC: budgetsense-vpc<br/>public + private subnets"]
    GitHub["GitHub Repo<br/>(audit trail: specs, ADRs, runbooks)"]

    Reviewer -->|"HTTPS request"| Internet
    Internet -->|"/health, /query"| CloudRun
    CloudRun -->|"private IP,<br/>via VPC connector"| CloudSQL
    CloudRun -->|"secretAccessor<br/>(scoped)"| SecretMgr
    CloudRun -.->|"pulls image at deploy"| ArtifactReg
    CloudRun -.->|"lives inside"| VPC
    CloudSQL -.->|"lives inside"| VPC
    Reviewer -->|"inspects build history"| GitHub

    style CloudSQL fill:#2d3748,stroke:#e53e3e
    style SecretMgr fill:#2d3748,stroke:#ecc94b
```

**Key property visible in this diagram:** Cloud SQL has no path to/from the public
internet at all. The _only_ way to reach it is through Cloud Run, through the VPC
connector, over a private IP.

---

## 3. Network Architecture (Epic 1)

```mermaid
graph TB
    subgraph VPC["budgetsense-vpc (custom-mode)"]
        subgraph Public["budgetsense-vpc-public — 10.10.0.0/24"]
            note1["reserved for future<br/>public-facing resources<br/>(none deployed yet)"]
        end
        subgraph Private["budgetsense-vpc-private — 10.10.1.0/24"]
            SQL["Cloud SQL<br/>private IP: 10.0.0.3"]
        end
        Connector["VPC Access Connector<br/>10.10.2.0/28"]
        PSA["Private Services Access<br/>peering range: /20"]
    end

    CloudRun["Cloud Run"] -->|"egress via"| Connector
    Connector -->|"reaches"| Private
    SQL -->|"provisioned via"| PSA

    FW1["allow-internal<br/>(subnet CIDRs only)"]
    FW2["allow-health-checks<br/>(GCP health-check ranges)"]
    FW3["allow-iap-ssh<br/>(IAP range, port 22 only)"]
    FW4["deny-all-ingress<br/>(0.0.0.0/0, priority 65534)"]
```

**Firewall posture:** default-deny, explicit-allow. As of ADR-003, all four rules
apply broadly (no target-tag requirement) — a deliberate simplicity-over-scoping
tradeoff for a solo-maintained project (documented tradeoff: `allow-iap-ssh` now
applies VPC-wide, mitigated by IAP still requiring an explicit IAM grant to connect).

**IaC status:** 100% of this layer is Terraform-managed (imported post-hoc from the
manual build — see ADR-001, ADR-002 in `docs/decisions.md`). `terraform plan` shows
zero drift.

---

## 4. Identity & Secrets Architecture (Epic 2 — partial)

```mermaid
graph LR
    SA["budgetsense-run-sa<br/>(dedicated service account)"]
    R1["roles/cloudsql.client<br/>(project-scoped)"]
    R2["roles/secretmanager.secretAccessor<br/>(scoped to 4 secrets only)"]
    S1["db-host"]
    S2["db-name"]
    S3["db-user"]
    S4["db-password"]

    SA --> R1
    SA --> R2
    R2 --> S1
    R2 --> S2
    R2 --> S3
    R2 --> S4
```

**Deliberate exclusions:** `budgetsense-run-sa` does NOT have:

- Project Editor/Owner
- Broad Secret Manager access (project-wide `secretAccessor`)
- Any Compute Engine or GKE-related roles (not needed, nothing runs there)

**Known gap (PRD Epic 2, Stories 2.4–2.5):** Cloud Audit Logs review and a full
project-wide IAM binding review have not yet been performed. This is the weakest
part of the current build and the next priority before claiming Epic 2 "Done."

---

## 5. Application Workload Architecture (Epic 3)

```mermaid
sequenceDiagram
    participant R as Reviewer
    participant CR as Cloud Run
    participant SM as Secret Manager
    participant SQL as Cloud SQL

    R->>CR: GET /health
    CR->>SM: resolve DB_HOST, DB_NAME,<br/>DB_USER, DB_PASSWORD (latest)
    Note over CR,SM: resolved once per<br/>container cold start
    CR->>SQL: connect (private IP) + SELECT NOW()
    SQL-->>CR: current timestamp
    CR-->>R: {"status":"healthy",<br/>"db_connected":true,...}
```

**Container:** Python 3.12-slim, FastAPI + Uvicorn, `psycopg2-binary` for a direct
private-IP Postgres connection (no Cloud SQL Auth Proxy needed, since private
networking is already established at the VPC layer).

**Scale-to-zero:** `min-instances=0`. No cost while idle — the defining cost
constraint for this whole project (ADR-002).

**Two real production-grade lessons surfaced during this Epic** (see
`specs/003-workload/runbook.md` for full detail):

1. Cloud Run's `latest` secret reference is resolved **once, at revision creation**
   — not dynamically. "Redeploy" on an existing revision does not re-resolve it; a
   genuinely new revision is required.
2. An invisible leading-space character in an environment variable name caused
   PostgreSQL to silently fall back to defaulting the database name to the
   connecting username — a subtle failure mode only diagnosable by comparing raw
   `gcloud describe --format=yaml` output against the Console UI.

---

## 6. Target Architecture — Remaining Epics

### 6.1 Observability (Epic 4, backlog)

```mermaid
graph LR
    CR["Cloud Run"] -->|metrics/logs| CM["Cloud Monitoring"]
    CR -->|logs| CL["Cloud Logging"]
    SQL["Cloud SQL"] -->|metrics| CM
    CM -->|alert policy| Notify["Notification channel<br/>(e.g. email)"]
    SCC["Security Command Center"] -.->|findings| Review["Manual triage"]
```

### 6.2 Governance (Epic 5, backlog)

Organization Policies applied at the project (or folder, if one exists) level:

- `constraints/gcp.resourceLocations` restricted to `australia-southeast1` /
  `australia-southeast2`
- `constraints/compute.vmExternalIpAccess` / equivalent Cloud SQL public-IP
  restriction, enforced as policy rather than relying on per-resource convention

### 6.3 Applied AI — RAG Layer (Epic 6, backlog)

```mermaid
graph LR
    Docs["Budget policy documents"] -->|upload| GCS["Cloud Storage"]
    GCS -->|parse| DocAI["Document AI"]
    DocAI -->|chunks| VertexIdx["Vertex AI<br/>Vector Search index"]
    Query["User question<br/>(via /query)"] -->|embed + search| VertexIdx
    VertexIdx -->|retrieved chunks| Gemini["Gemini<br/>(grounded generation)"]
    Gemini -->|cited answer| Response["/query response"]
```

This mirrors [[budgetsense-ai]]'s AWS architecture (Bedrock/Claude + pgvector hybrid
search) using GCP-native equivalents — the explicit "same problem, ported cloud"
story referenced in the Project Brief.

---

## 7. Cross-Cutting Decisions (index into `docs/decisions.md`)

| ADR     | Decision                                  | Epic |
| ------- | ----------------------------------------- | ---- |
| ADR-001 | Manual Console build before Terraform     | 1    |
| ADR-002 | Cloud Run over GKE (cost-driven)          | 3    |
| ADR-003 | Untagged (broadly-applied) firewall rules | 1    |

Future architectural decisions (e.g. how Epic 6's vector index is structured, or
whether Epic 5's policies apply project- or folder-wide) will be added here as
ADR-004+ when made.

---

## 8. Non-Functional Requirements Summary

| Requirement                      | Current Status                                                                                                     |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| $0 idle cost                     | ✅ Cloud Run min-instances=0; no GKE cluster fee                                                                   |
| Data residency (AU regions only) | 🟡 Convention-enforced (all resources manually placed in `australia-southeast1`); NOT yet policy-enforced (Epic 5) |
| No public database access        | ✅ Cloud SQL private-IP only                                                                                       |
| No secrets in code/images        | ✅ All 4 DB credentials via Secret Manager                                                                         |
| Least-privilege identity         | 🟡 Workload SA is scoped correctly; full IAM audit not yet performed (Epic 2)                                      |
| IaC-managed foundation           | ✅ Epic 1 fully Terraform-imported and drift-free                                                                  |

## 9. Target End-State Architecture (Reference)

The diagrams in §6.3 (Applied AI — RAG Layer) reflect Epic 6's current committed
scope. The full product vision (see `docs/PRD.md` §7) implies a richer version of
that layer:

**Additional components beyond Epic 6's current diagram:**

| Component              | GCP Service                                         | Role                                                                                                                                                                                                                                    |
| ---------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Agent orchestrator     | Cloud Run (extends the existing API service)        | Runs the ReAct control loop in application code — not a separate managed agent product, so the reasoning stays auditable in-repo                                                                                                        |
| Hybrid retrieval store | Cloud SQL + `pgvector` (reuses the Epic 3 instance) | Dense vector + native full-text (BM25-style) search combined via Reciprocal Rank Fusion, plus an authority-tier weighting column — mirrors [[budgetsense-ai]]'s AWS design more closely than a pure Vertex AI Vector Search index would |
| Semantic cache         | Memorystore for Redis                               | GCP equivalent of BudgetSense's ElastiCache Redis; cuts latency and Gemini token cost on repeated/similar questions                                                                                                                     |
| Agent actions          | Cloud Tasks + Cloud Functions                       | Decoupled from the request/response cycle — the agent queues a task rather than executing an action synchronously and unpredictably inline                                                                                              |
| Trust badge            | Computed in the API layer (no new service)          | Derived from source authority tier + retrieval confidence + citation coverage                                                                                                                                                           |

**Why this isn't in §6.3 as committed architecture yet:** these components
represent a larger scope than Epic 6's current Stories commit to (see PRD §7 for
the scope boundary). This section exists so the target shape is documented before
it's built, consistent with this project's spec-before-code discipline — but it is
explicitly a reference, not yet a spec.
