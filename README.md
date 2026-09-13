# BudgetSense-GCP

A GCP-native rebuild of BudgetSense — a hybrid RAG platform for querying Australian
Federal Budget policy — built as a portfolio project demonstrating secure,
production-grade Google Cloud architecture (compute, networking, identity,
observability, governance, and Vertex AI).

Built using **Spec-Driven Development**: every feature starts as a written spec in
[`/specs`](./specs) before any code is written, so the commit history documents the
full design process from decision to implementation.

## Status

🚧 In progress — see [`docs/project-brief.md`](./docs/project-brief.md) for scope and
[`specs/`](./specs) for the current build log.

## Repo Structure

```
docs/           Project brief, architecture decisions, diagrams
specs/          Numbered specs — one per capability/feature, written before code
infra/          Terraform / IaC for GCP resources
src/            Application code (API, frontend, ingestion pipeline)
```

## Architecture Pillars

| Pillar | GCP Services |
|---|---|
| Compute | Cloud Run |
| Data | Cloud SQL, Cloud Storage |
| Identity | IAM (custom roles), Cloud Audit Logs |
| Networking | VPC, private subnets, firewall rules |
| Observability | Cloud Monitoring, Cloud Logging, Security Command Center |
| Governance | Organization Policies (data residency, public-IP restrictions) |
| AI/ML | Vertex AI, Document AI, Gemini |


