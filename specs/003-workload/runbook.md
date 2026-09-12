# step-by-step log of the manual console build

# Runbook: Spec 003 — Workload (Manual Build Log)

## Cloud SQL

| Field        | Value                                                               |
| ------------ | ------------------------------------------------------------------- |
| Instance ID  | `budgetsense-db`                                                    |
| Engine       | PostgreSQL                                                          |
| Region       | `australia-southeast1`                                              |
| Connectivity | Private IP only (no public IP), via Phase 1 private services access |
| Database     | `budgetsense`                                                       |
| App user     | `budgetsense_app` (non-superuser, dedicated to the application)     |

## Secret Manager

| Secret        | Purpose              |
| ------------- | -------------------- |
| `db-host`     | Cloud SQL private IP |
| `db-name`     | `budgetsense`        |
| `db-user`     | `budgetsense_app`    |
| `db-password` | App user's password  |

All four scoped to `budgetsense-run-sa` only, via per-secret `Secret Manager Secret Accessor` grants — not project-wide access.

## Service Account

| Field | Value                                                                                                         |
| ----- | ------------------------------------------------------------------------------------------------------------- |
| Name  | `budgetsense-run-sa`                                                                                          |
| Roles | `roles/cloudsql.client` (project-level); `roles/secretmanager.secretAccessor` (scoped to the 4 secrets above) |

## Artifact Registry

| Field      | Value                  |
| ---------- | ---------------------- |
| Repository | `budgetsense-images`   |
| Format     | Docker                 |
| Region     | `australia-southeast1` |
| Image      | `budgetsense-app:v1`   |

## Cloud Run

| Field           | Value                                                                |
| --------------- | -------------------------------------------------------------------- |
| Service name    | `budgetsense-app-v1`                                                 |
| Region          | `australia-southeast1`                                               |
| Auth            | Unauthenticated (public) — matches spec, no auth required this phase |
| Service account | `budgetsense-run-sa` (not default)                                   |
| VPC connector   | `budgetsense-connector` (Phase 1), routing only private-IP traffic   |
| Min instances   | 0 (true scale-to-zero)                                               |
| Live URL        | `https://budgetsense-app-401917747007.australia-southeast1.run.app`  |

## Verification

`GET /health` returns:

```json
{ "status": "healthy", "db_connected": true, "db_time": "..." }
```

Confirms the full path: Cloud Run → VPC connector → private subnet → Cloud SQL private IP.

## Deviations From Spec / Issues Hit

1. **Duplicate/misnamed Cloud Run service.** Initially deployed as `budgetsense-app` before diagnosing the issue below; a second service `budgetsense-app-v1` was created during debugging and became the final, correct one. The original `budgetsense-app` was deleted once `-v1` was confirmed healthy.

2. **Stale secret resolution on Redeploy.** Cloud Run resolves a `latest` secret reference once, at revision creation — clicking "Redeploy" on an existing revision does NOT re-resolve it. A genuinely new revision (`gcloud run services update`, or Edit & Deploy New Revision) is required to pick up a new secret version.

3. **Root cause of the actual connection failure:** the `DB_NAME` environment variable name had an invisible leading space (`" DB_NAME"` vs `"DB_NAME"`), introduced via a Console text field. This meant `os.environ.get("DB_NAME")` returned `None` in the app, and PostgreSQL's client library silently defaulted the missing database name to match the connecting username — producing the misleading error `database "budgetsense_app" does not exist`. Diagnosed by comparing `gcloud run services describe ... --format="yaml(...)"` raw output against the Console UI, which visually hid the leading space. **Lesson: verify infrastructure config via CLI/YAML output, not just UI screenshots, when something doesn't add up.**
