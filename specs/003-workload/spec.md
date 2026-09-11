# Spec 003: Workload — Cloud Run, Cloud SQL, Secret Manager

## Status

Draft → Implementing (manual, via Console)

## 1. Problem

Phase 1 built the network (VPC, subnets, firewall, private services access) but has
nothing running on it. This spec adds the actual application workload: a Python
service on Cloud Run, backed by a Cloud SQL database reachable only over private IP,
with credentials held in Secret Manager rather than in code or environment files.

This is also the first phase where something is genuinely live and demoable — a
deployed, reachable service — rather than pure infrastructure.

## 2. Requirements

### 2.1 Cloud SQL

- PostgreSQL instance (matches BudgetSense's original Postgres/pgvector design intent
  on AWS — GCP's managed Postgres is the natural equivalent here).
- **Private IP only** — no public IP assigned. Reachable exclusively via the private
  services access peering set up in Phase 1.
- Located in `australia-southeast1`, same region as everything else.
- A dedicated application database and a dedicated (non-default) database user —
  not using the `postgres` superuser for the app's own connections.

### 2.2 Secret Manager

- Database connection details (host, database name, username, password) stored as
  Secret Manager secrets, not hardcoded or placed in a `.env` file that gets deployed.
- Cloud Run's service account granted `roles/secretmanager.secretAccessor` scoped to
  just the secrets it needs — not project-wide Secret Manager access.

### 2.3 Artifact Registry

- A Docker repository (already created in an earlier exploratory step —
  `budgetsense-images`, region `australia-southeast1`) holds the container image
  Cloud Run deploys.

### 2.4 Cloud Run

- Python service (framework choice — e.g. FastAPI or Flask — decided at
  implementation time; this spec doesn't mandate one).
- Deployed with a **VPC connector** attached (the `budgetsense-connector` from Phase
  1), so it can reach Cloud SQL over private IP.
- Runs as a **dedicated service account** (not the default Compute Engine service
  account) with least-privilege roles: Secret Manager accessor (scoped, per §2.2) and
  Cloud SQL Client (`roles/cloudsql.client`).
- Publicly invokable for this phase (no auth required to hit the endpoint) — auth/
  IAP restriction is a candidate for a later spec, not required here.
- Min instances 0 (true scale-to-zero, keeping cost at zero when idle) — an explicit,
  deliberate choice given the project's zero-budget goal (see `docs/decisions.md`
  ADR-002).

### 2.5 Application Behaviour (minimum viable, this spec)

- A single endpoint (e.g. `/health` or `/`) that connects to Cloud SQL and returns a
  simple confirmation (e.g. current timestamp from the database) — proves the private
  networking path actually works end-to-end: Cloud Run → VPC connector → private
  subnet → Cloud SQL private IP.
- Does **not** yet include the RAG/AI logic — that's Spec 004+ (AI Layer). This spec
  is purely "can the workload reach its database privately and securely."

### 2.6 Implementation Method

- **Manual, via GCP Console** — same approach as Phase 1, for the same reason: build
  hands-on understanding before automating. Logged in
  `specs/003-workload/runbook.md` as it's done.
- Terraform import as a follow-up, once manually verified working (Phase 3b),
  mirroring the Phase 1 → 1b pattern.

## 3. Non-goals (this spec)

- No RAG/AI logic yet (Spec 004+).
- No custom domain / HTTPS load balancer — Cloud Run's default `*.run.app` URL is
  sufficient for this phase.
- No authentication on the Cloud Run endpoint yet.
- No CI/CD pipeline — image build and deploy are manual (`gcloud run deploy`) for now.

## 4. Acceptance Criteria

- [ ] Cloud SQL instance created, private IP only, reachable from Cloud Run but not
      from the public internet.
- [ ] Dedicated app database and non-superuser DB user created.
- [ ] DB credentials stored in Secret Manager; Cloud Run's service account has
      scoped `secretAccessor` access only to those secrets.
- [ ] Cloud Run service deployed with the VPC connector attached, running as a
      dedicated (non-default) service account with least-privilege roles.
- [ ] Hitting the Cloud Run URL's health endpoint returns a successful response that
      proves a live database round-trip.
- [ ] Min instances = 0 confirmed (service scales to zero when idle).
- [ ] `specs/003-workload/runbook.md` records every step, resource name, and
      configuration value used.

## 5. Files Introduced
