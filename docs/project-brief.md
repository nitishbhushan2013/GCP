# Project Brief: BudgetSense-GCP

## 1. Purpose

A hands-on, end-to-end portfolio project rebuilding [BudgetSense](../README.md) — a hybrid
RAG platform for querying Australian Federal Budget policy — natively on Google Cloud
Platform. The project exists to demonstrate broad, applied GCP proficiency (compute,
data, networking, identity, observability, governance, and AI/ML) for a Department of
Defence role application, using an architecture and level of rigour appropriate to that
context (security, auditability, data residency).

This is **not** a lift-and-shift of the AWS original. It is a fresh, GCP-native design
that solves the same problem — hybrid retrieval-augmented Q&A over budget policy
documents — using GCP's equivalent and idiomatic services.

## 2. Background

The original BudgetSense runs on AWS (Aurora PostgreSQL + pgvector, ElastiCache Redis,
Bedrock/Claude, Spring Boot on EKS, Next.js, Terraform) using hybrid search (BM25 +
dense vector + RRF) with authority-tier score weighting. BudgetSense-GCP reuses the same
problem domain and product intent, but is architected around GCP-native primitives.

## 3. Deliverable

A live, demoable, end-to-end application — not just a checklist of services used —
that a technical reviewer can:

- **Open and use**: ask a budget-policy question, get a grounded, cited answer.
- **Inspect**: read the architecture and see *why* each decision was made.
- **Audit**: review the full build history on GitHub, spec by spec, commit by commit.

The deliverable is evaluated against five capability pillars:

| Pillar | Demonstrated via |
|---|---|
| Secure architecture | VPC design, network segmentation, no public DB access |
| Identity & access control | Custom least-privilege IAM roles |
| Observability | Real Cloud Monitoring dashboards & log-based alerts |
| Compliance & governance | Organization Policies enforcing AU data residency |
| Applied AI | Working RAG pipeline with grounded, citation-backed answers |

## 4. Methodology

Built using **Spec-Driven Development (SDD)**: every capability is defined as a written
spec *before* code is written. Specs live in `/specs/`, numbered sequentially, and are
committed independently of their implementation so the GitHub history itself tells the
story of the design process — this is the "auditable source" requirement.

Workflow per spec:
1. Write the spec (`/specs/NNN-name/spec.md`) — problem, requirements, acceptance criteria.
2. Review/refine the spec with Claude before any code is written.
3. Implement against the spec.
4. Commit spec and implementation together (or spec first, implementation as a
   follow-up commit) with a message referencing the spec number.

## 5. Scope — Phases (from the GCP Defence Showcase plan)

1. **Foundation** — GCP project setup, VPC (public/private subnets), firewall rules
2. **Identity** — custom least-privilege IAM roles, Cloud Audit Logs
3. **Workload** — API + frontend on Cloud Run (private), Cloud SQL, Secret Manager
4. **Monitoring** — Cloud Monitoring dashboards, Cloud Logging sinks, Security Command Center
5. **Governance** — Organization Policies (block public IPs, restrict region to `australia-southeast1`)
6. **AI Layer** — RAG pipeline: Cloud Storage (source docs) → Document AI (parsing) →
   Vertex AI (vector index / search) → Gemini (generation), fronted by Cloud Run

## 6. Out of scope (for now)

- Multi-region / DR architecture
- CI/CD pipeline hardening beyond a basic Cloud Build trigger
- Load testing / performance benchmarking
- Cost optimization pass

## 7. Success Criteria

- [ ] Application is deployed and reachable
- [ ] A budget-policy question produces a grounded, cited answer
- [ ] Architecture diagram exists and matches deployed reality
- [ ] Every phase has a corresponding spec in `/specs/` and a matching implementation commit
- [ ] No secrets in git history; no public IP on the database
- [ ] Reviewer can trace any design decision back to its spec
