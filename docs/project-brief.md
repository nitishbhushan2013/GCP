# Project Brief: BudgetSense-GCP

## 1. Purpose

A hands-on, end-to-end portfolio project rebuilding [BudgetSense](../README.md) — a hybrid
RAG platform for querying Australian Federal Budget policy — natively on Google Cloud
Platform. The project exists to demonstrate broad, applied GCP proficiency (compute,
data, networking, identity, observability, governance, and AI/ML) and level of rigour appropriate to that
context (security, auditability, data residency).

It is a fresh, GCP-native design that solves the same problem — hybrid retrieval-augmented Q&A over budget policy
documents — using GCP's equivalent and idiomatic services.

## 2. Deliverable

The deliverable is evaluated against five capability pillars:

| Pillar                    | Demonstrated via                                            |
| ------------------------- | ----------------------------------------------------------- |
| Secure architecture       | VPC design, network segmentation, no public DB access       |
| Identity & access control | Custom least-privilege IAM roles                            |
| Observability             | Real Cloud Monitoring dashboards & log-based alerts         |
| Compliance & governance   | Organization Policies enforcing AU data residency           |
| Applied AI                | Working RAG pipeline with grounded, citation-backed answers |

The deliverable must also be **independently accessible** —anyone can open a URL
on their own schedule and interact with the system directly, without a live session or
credential exchange with the project owner (see ADR-008 in `docs/decisions.md`).

## 4. Methodology

Built using **Spec-Driven Development (SDD)**: every capability is defined as a written
spec _before_ code is written. Specs live in `/specs/`, numbered sequentially, and are
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
   _(Note: frontend was deferred out of Phase 3/Epic 3's initial build — API-only
   shipped first to prove the private-networking path end-to-end. Delivered later
   as Epic 7, once Epic 6's RAG API existed to give the frontend something
   meaningful to call.)_
4. **Monitoring** — Cloud Monitoring dashboards, Cloud Logging sinks, Security Command Center
5. **Governance** — Organization Policies (block public IPs, restrict region to `australia-southeast1`)
6. **AI Layer** — RAG pipeline: Cloud Storage (source docs) → Document AI (parsing) →
   Vertex AI (vector index / search) → Gemini (generation), fronted by Cloud Run
7. **Web UI** — a public-facing demo interface over the Epic 6 API, deployed on the
   existing Cloud Run service with no new infrastructure (see `docs/PRD.md` Epic 7)

## 6. Out of scope (for now)

- Multi-region / DR architecture
- CI/CD pipeline hardening beyond a basic Cloud Build trigger
- Load testing / performance benchmarking
- Cost optimization pass
- Abuse-prevention controls on the public UI (rate limiting, API keys) beyond what's
  noted as a future revisit trigger in ADR-008

## 7. Success Criteria

- [x] Application is deployed and reachable
- [x] A budget-policy question produces a grounded, cited answer
- [ ] A reviewer can interact with the system through a browser, not just curl/Postman,
      at any time, without a live session with the project owner (Epic 7, pending
      local + production verification)
- [ ] Architecture diagram exists and matches deployed reality
- [x] Every phase has a corresponding spec in `/specs/` and a matching implementation commit
- [x] No secrets in git history; no public IP on the database

8. **Agentic Retrieval** — multi-hop reasoning (ReAct) over the Epic 6 RAG
   pipeline, to correctly answer compound, multi-topic citizen questions
   that a single-pass retrieval can't represent well (see `docs/PRD.md`
   Epic 8, ADR-010)
