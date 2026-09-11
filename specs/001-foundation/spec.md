# Spec 001: Foundation — GCP Project, VPC & Network Segmentation

## Status
Draft → Implementing (manually, via Console)

## 1. Problem

Before any workload, identity, or AI component can exist, the project needs a GCP
project and a properly segmented network. Everything downstream (Cloud Run, Cloud SQL,
IAM, monitoring) depends on this foundation being correct — in particular, the database
must never be reachable from the public internet, and all resources must be pinned to
an Australian region to support the data-residency story.

## 2. Requirements

### 2.1 GCP Project
- Single GCP project, e.g. `budgetsense-gcp-prod`.
- Billing account linked.
- Required APIs enabled: Compute Engine, Cloud Run, Cloud SQL Admin, Secret Manager,
  VPC Access, Cloud Resource Manager, IAM, Cloud Logging, Cloud Monitoring,
  Service Networking.

### 2.2 Region
- All resources pinned to **`australia-southeast1`** (Sydney). No cross-region
  resources in this phase.

### 2.3 VPC
- One custom-mode VPC (not the GCP default auto-mode VPC — default VPCs are broad and
  not appropriate to show good practice).
- Two subnets in `australia-southeast1`:
  - `public-subnet` — for anything that needs a public-facing entry point later
    (e.g. a load balancer). No compute placed here directly in this phase.
  - `private-subnet` — for Cloud SQL (via private services access) and Cloud Run
    (via Serverless VPC Access connector). No resource here gets a public IP.
- A **Serverless VPC Access connector** in the private subnet's range, so Cloud Run can
  reach the private subnet in Phase 3.
- **Private Services Access** (VPC peering for Google-managed services) configured so
  Cloud SQL can use a private IP with no public IP at all.

### 2.4 Firewall Rules
Default-deny posture; explicit allow rules only:
- Allow internal traffic between the two subnets (for future service-to-service calls).
- Allow health-check ranges (`130.211.0.0/22`, `35.191.0.0/16`) for future load
  balancer/Cloud Run health checks.
- Allow SSH (22) **only** from Identity-Aware Proxy's range (`35.235.240.0/20`), never
  from `0.0.0.0/0` — the standard "no bastion, no open SSH" pattern.
- No rule permits unrestricted ingress from `0.0.0.0/0` on any port.

### 2.5 Implementation Method
- **Phase 1 (this spec): manual, via GCP Console.** Built by hand, screen by screen,
  so every setting is understood before it's automated — not copy-pasted from a
  template. Each step taken is logged in `specs/001-foundation/runbook.md` as it's
  done, so the repo still documents the *how*, not just the *what*.
- **Phase 1b (later, optional): Terraform.** Once the manual build is verified working,
  the same resources may be re-expressed as Terraform as a separate follow-up spec —
  this mirrors how teams often prototype by hand before committing to IaC.

## 3. Non-goals (this spec)
- No compute or database resources yet (that's Phase 3).
- No load balancer / public entry point yet.
- No Terraform / IaC yet (deferred to Phase 1b).

## 4. Acceptance Criteria
- [ ] GCP project created, billing linked, required APIs enabled.
- [ ] Custom-mode VPC created with 2 subnets, both in `australia-southeast1`.
- [ ] Serverless VPC Access connector created in the private subnet's range.
- [ ] Private Services Access configured (peering to `servicenetworking.googleapis.com`).
- [ ] Firewall rules match §2.4 exactly — verified no rule allows `0.0.0.0/0` on any
      admin port.
- [ ] `specs/001-foundation/runbook.md` records every step taken, with screenshots or
      exact values used (subnet CIDRs, resource names) so the build is reproducible.
- [ ] `docs/decisions.md` records the manual-first approach and the plan to
      Terraform-ify later.

## 5. Files Introduced
```
specs/001-foundation/runbook.md   # step-by-step log of the manual console build
docs/decisions.md                  # architecture decision log (new file, started here)
```
Terraform files (if/when Phase 1b happens) will be introduced in a follow-up spec.
