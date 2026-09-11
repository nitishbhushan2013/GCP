# Runbook: Spec 001 — Foundation (Manual Build Log)

This is the as-built record of the manual GCP Console setup for Spec 001, so the
repo documents exactly what was built, not just what was planned.

## Project

| Field          | Value                  |
| -------------- | ---------------------- |
| Project name   | `budgetsense-gcp-prod` |
| Project ID     | `budgetsense-gcp-prod` |
| Project number | `401917747007`         |
| Region         | `australia-southeast1` |
| Billing        | Linked                 |

## APIs Enabled

- Compute Engine API
- Cloud Run Admin API
- Cloud SQL Admin API
- Secret Manager API
- Serverless VPC Access API
- Cloud Resource Manager API
- Identity and Access Management (IAM) API
- Cloud Logging API
- Cloud Monitoring API
- Service Networking API

## VPC

| Field    | Value             |
| -------- | ----------------- |
| VPC name | `budgetsense-vpc` |
| Mode     | Custom (not Auto) |

### Subnets

| Name                      | Region                 | CIDR           | Private Google Access |
| ------------------------- | ---------------------- | -------------- | --------------------- |
| `budgetsense-vpc-public`  | `australia-southeast1` | `10.10.0.0/24` | Off                   |
| `budgetsense-vpc-private` | `australia-southeast1` | `10.10.1.0/24` | On                    |

### Serverless VPC Access Connector

| Field   | Value                   |
| ------- | ----------------------- |
| Name    | `budgetsense-connector` |
| Region  | `australia-southeast1`  |
| Network | `budgetsense-vpc`       |
| Range   | `10.10.2.0/28`          |

### Private Services Access

| Field               | Value                              |
| ------------------- | ---------------------------------- |
| Reserved range name | `budgetsense-vpc-psa-range`        |
| Purpose             | Peering range (VPC peering)        |
| Prefix length       | `/20`                              |
| Peered service      | `servicenetworking.googleapis.com` |

## Firewall Rules

| Name                  | Direction | Source ranges                                  | Target tags   | Action                |
| --------------------- | --------- | ---------------------------------------------- | ------------- | --------------------- |
| `allow-internal`      | Ingress   | `10.10.0.0/24`, `10.10.1.0/24`, `10.10.2.0/28` | All instances | Allow (TCP/UDP/ICMP)  |
| `allow-health-checks` | Ingress   | `130.211.0.0/22`, `35.191.0.0/16`              | All instances | Allow (TCP)           |
| `allow-iap-ssh`       | Ingress   | `35.235.240.0/20`                              | `iap-ssh`     | Allow (TCP:22)        |
| `deny-all-ingress`    | Ingress   | `0.0.0.0/0`                                    | All instances | Deny (priority 65534) |

No rule permits `0.0.0.0/0` ingress on any admin port — confirmed against Spec 001 §4.

## Deviations from Spec

None — all values match `specs/001-foundation/spec.md` §2 exactly.

## Notes

- Built via GCP Console, screen by screen, per the spec's "manual first" approach
  (see `docs/decisions.md` ADR-001).
- GKE was briefly evaluated as a workload option instead of Cloud Run but reverted —
  see `docs/decisions.md` ADR-002 for the cost rationale. This foundation (VPC,
  subnets, connector, PSA) is unaffected by that decision either way.spec   
