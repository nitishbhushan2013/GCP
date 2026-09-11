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
