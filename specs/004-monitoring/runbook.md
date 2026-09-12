# Runbook: Spec 004 — Observability & Monitoring

## Cloud Monitoring Dashboard

**Name:** BudgetSense - System Health

| Widget         | Metric                                        | Filter                            |
| -------------- | --------------------------------------------- | --------------------------------- |
| Request count  | Cloud Run Revision → Request count            | `service_name=budgetsense-app-v1` |
| Latency (p95)  | Cloud Run Revision → Request latencies        | 95th percentile aggregation       |
| Instance count | Cloud Run Revision → Container instance count | `service_name=budgetsense-app-v1` |
| Error rate     | Cloud Run Revision → Request count            | grouped by `response_code_class`  |
| DB connections | Cloud SQL Database → connections              | `budgetsense-db`                  |
| DB CPU         | Cloud SQL Database → CPU utilization          | `budgetsense-db`                  |
| DB memory      | Cloud SQL Database → Memory utilization       | `budgetsense-db`                  |

## Alert Policy

**Log-based metric:** `unhealthy-response-count` (Counter)
Filter: `resource.type="cloud_run_revision" AND resource.labels.service_name="budgetsense-app-v1" AND jsonPayload.status="unhealthy"`

**Alert policy:** BudgetSense - Unhealthy Response Detected
Condition: metric count > 0 over a 1-minute window
Notification: email

**Proven working, not just configured.** Deliberately broke the `db-password` secret
(new version with a wrong value), forced a fresh Cloud Run revision to pick it up
on cold start, hit `/health` to trigger real `"status":"unhealthy"` responses, and
confirmed the alert email arrived. Restored the correct password afterward and
verified `/health` returned to `"status":"healthy"`.

## Security Command Center

Attempted to open Security Command Center via the Console. Received:

> "You need to be part of an organization in order to use Security Command Center.
> If you already have an organization, reload this page, or reach out to Google
> Support."

**Finding:** Full Security Command Center requires a GCP Organization resource,
which a personal/solo Google account project does not have by default (an
Organization is normally tied to a Google Workspace or Cloud Identity domain).
This is a structural limitation of the account type, not a misconfiguration —
documented and accepted rather than worked around, since creating an organization
purely to unlock this feature would be disproportionate for a portfolio project.

**What this means practically:** security posture visibility for this project
relies on the IAM review (Epic 2), the Cloud Audit Logs (Epic 2), and this Epic's
Cloud Monitoring dashboard/alerting — not on SCC's automated finding detection,
which isn't accessible at this account tier.

## Outcome

- Dashboard: 7 widgets covering Cloud Run and Cloud SQL health, live and usable
- Alert: created, and proven to genuinely fire via a deliberate test — not just configured
- SCC: attempted, found to require an Organization; documented as an account-tier limitation rather than left unexplained
