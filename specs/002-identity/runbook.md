# Runbook: Spec 002 — Identity & Access Governance (Retrofit)

## IAM Bindings Review

Full project IAM policy reviewed via `gcloud projects get-iam-policy budgetsense-gcp-prod`.

| Principal                                            | Role                                       | Classification                                                                                                                       | Action                                                                                                                                                                                   |
| ---------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `service-...@gcp-sa-artifactregistry...`             | `artifactregistry.serviceAgent`            | Expected (Google-managed default)                                                                                                    | None                                                                                                                                                                                     |
| `budgetsense-run-sa`                                 | `roles/cloudsql.client`                    | Expected, correctly scoped                                                                                                           | None                                                                                                                                                                                     |
| `...@cloudservices.gserviceaccount.com`              | `compute.instanceGroupManagerServiceAgent` | Expected (Google-managed default)                                                                                                    | None                                                                                                                                                                                     |
| `service-...@compute-system...`                      | `compute.serviceAgent`                     | Expected (Google-managed default)                                                                                                    | None                                                                                                                                                                                     |
| `service-...@containerregistry...`                   | `containerregistry.ServiceAgent`           | Legacy, unused (superseded by Artifact Registry) but Google-managed and low-risk                                                     | Accepted as-is — not worth removing a Google service agent for a service we don't actively use                                                                                           |
| `401917747007-compute@developer.gserviceaccount.com` | `roles/editor`                             | **Over-broad — real finding**                                                                                                        | **Removed.** Nothing in this project uses the default Compute Engine SA; the workload runs as the dedicated `budgetsense-run-sa` instead                                                 |
| `401917747007@cloudservices.gserviceaccount.com`     | `roles/editor`                             | Over-broad in principle, but Google-managed and used internally for project-level automation (API enablement, background operations) | **Accepted, documented.** Removing risks breaking basic project functionality for uncertain security benefit, since this account isn't attacker-reachable the way a workload SA would be |
| `nitishbhushanai@gmail.com`                          | `roles/owner`                              | Expected — account holder                                                                                                            | None                                                                                                                                                                                     |
| `service-...@gcp-sa-pubsub...`                       | `pubsub.serviceAgent`                      | Expected (Google-managed default)                                                                                                    | None                                                                                                                                                                                     |
| `service-...@serverless-robot-prod...`               | `run.serviceAgent`                         | Expected — required for Cloud Run                                                                                                    | None                                                                                                                                                                                     |
| `service-...@service-networking...`                  | `servicenetworking.serviceAgent`           | Expected — required for Epic 1 Private Services Access                                                                               | None                                                                                                                                                                                     |
| `service-...@gcp-sa-vpcaccess...`                    | `vpcaccess.serviceAgent`                   | Expected — required for Epic 1 VPC connector                                                                                         | None                                                                                                                                                                                     |

**Per-secret bindings** (checked separately, since these are resource-level, not project-level):
All four secrets (`db-host`, `db-name`, `db-user`, `db-password`) have exactly one binding each: `budgetsense-run-sa` with `roles/secretmanager.secretAccessor`. No broader or unexpected grants found. ✅ Matches Epic 3 design exactly.

**Fix applied:** removed `roles/editor` from `401917747007-compute@developer.gserviceaccount.com` via:
gcloud projects remove-iam-policy-binding budgetsense-gcp-prod --member="serviceAccount:401917747007-compute@developer.gserviceaccount.com" --role="roles/editor"

Verified via a follow-up `get-iam-policy` — binding successfully removed, all other bindings unchanged.

## Cloud Audit Logs Review

**Data Access logging enabled** (via Console: IAM & Admin → Audit Logs) for:

- Secret Manager (Data Read, Data Write)
- Cloud SQL Admin API (Data Read, Data Write)

**Finding 1 — Secret Manager logging confirmed working end-to-end.**
Forced a fresh Cloud Run revision (`gcloud run services update ... --update-env-vars=AUDIT_TEST=1`) to trigger a genuine cold-start secret read, then queried Logs Explorer:
protoPayload.serviceName="secretmanager.googleapis.com"

Found a real `AccessSecretVersion` log entry with `principalEmail: budgetsense-run-sa@budgetsense-gcp-prod.iam.gserviceaccount.com` — confirms the correct, least-privilege identity is the one actually accessing secrets, and that access is genuinely logged (who, what, when).

**Finding 2 — Cloud SQL query/connection-level access is NOT captured by Cloud Audit Logs**, despite Data Access logging being enabled.

Root cause: Cloud SQL's Cloud Audit Logs only cover the **Admin API** (`sqladmin.googleapis.com`) — operations like creating databases/users/instances. They do not capture actual SQL-level activity (queries, connections) made via the native Postgres wire protocol, which is how the application connects. To get genuine query/connection-level auditing, Cloud SQL requires enabling the **pgAudit** PostgreSQL extension via a database instance flag — a separate mechanism from project-level Cloud Audit Logs configuration.

**Decision:** Not enabling pgAudit in this spec — it's a real capability gap worth knowing about and documenting, but adding it is scoped as a candidate for a future spec (see below) rather than blocking Epic 2's closure. The distinction between infrastructure-level and data-level audit logging is itself the key finding here.

## Outcome

- IAM review: complete, one real finding (over-broad Editor on default Compute SA), fixed
- Audit logs: Secret Manager access logging confirmed working with a real captured event; Cloud SQL logging enabled but found to only cover Admin API operations, not query-level access — documented as a known GCP behavior, with pgAudit noted as the correct follow-up if deeper Cloud SQL auditing is needed later

## Candidate Future Spec

**pgAudit for Cloud SQL** — enable the `pgaudit` database flag on the Cloud SQL instance to get genuine SQL-level audit logging (connections, queries), closing the gap identified above. Not required for Epic 2 to be marked Done, but flagged here for future work.
