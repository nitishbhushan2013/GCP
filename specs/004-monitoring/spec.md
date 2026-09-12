# Spec 004: Observability & Monitoring

## Status

Draft → Implementing (manual, via Console)

## 1. Problem

Epics 1–3 built a working, privately-networked system, but nothing currently makes
its health or security posture _visible_. If Cloud Run started failing, or Cloud
SQL connections spiked, there is no dashboard, no alert, no signal — you'd only find
out by manually checking `/health`. This spec closes that gap: the system should be
observable, not just assumed-healthy.

## 2. Requirements

### 2.1 Cloud Monitoring Dashboard (PRD Story 4.1)

- A single custom dashboard showing, at minimum:
  - Cloud Run: request count, request latency (p50/p95), container instance count,
    error rate (4xx/5xx)
  - Cloud SQL: active connections, CPU utilization, memory utilization
- Should be usable as a genuine "is the system healthy right now" screen, not just
  a proof it exists.

### 2.2 Log-Based Alert (PRD Story 4.2)

- At least one alert policy that would actually catch a real problem, wired to a
  notification channel (email is sufficient).
- Candidate conditions (pick at least one, more if useful):
  - Cloud Run 5xx error rate exceeds a threshold over a time window
  - A log-based metric counting `"status":"unhealthy"` responses from `/health`
    exceeding a threshold
- The alert must be testable — this spec isn't done until the alert has actually
  fired at least once from a deliberately triggered condition, not just configured
  and assumed to work.

### 2.3 Security Command Center Review (PRD Story 4.3)

- Review whatever findings SCC's free tier surfaces for this project (note: full
  SCC requires an organization, which this personal/solo GCP account does not have
  — see runbook for what's actually accessible without one).
- Any actionable finding is either fixed or explicitly accepted with a documented
  reason — same discipline as the Epic 2 IAM review.

## 3. Non-goals

- No uptime/SLA guarantees or synthetic monitoring checks from external locations.
- No integration with a third-party incident tool (PagerDuty, Opsgenie, etc.) —
  email notification is sufficient for a solo portfolio project.
- Organization Policies (Epic 5) are separate from this spec, even though SCC
  findings sometimes suggest policy fixes — a suggested policy fix found here gets
  _noted_ for Epic 5, not implemented here.

## 4. Acceptance Criteria

- [ ] Custom Cloud Monitoring dashboard created with the metrics listed in §2.1.
- [ ] At least one alert policy created and connected to a notification channel.
- [ ] The alert has been proven to fire at least once via a deliberately triggered
      condition (not just configured and left untested).
- [ ] Security Command Center reviewed; findings (or the lack of access without an
      org) documented with what was actually checked.
- [ ] `specs/004-monitoring/runbook.md` records dashboard configuration, the alert
      policy, the test that proved it fires, and SCC findings.

## 5. Files Introduced

```
specs/004-monitoring/runbook.md
```
