---
name: Avilex offer and positioning
description: What Avilex sells, how the two outreach modes differ, and the approved credential claims that may appear in outbound emails
type: project
---

Avilex (avilx.com) is Prem Vishnoi's data engineering / AI delivery firm, based in Ha Noi, Vietnam.
Positioning used in outreach: a global senior-only engineering pod (6–20 engineers, avg 8+ yrs)
across 7+ clouds (AWS · Azure · GCP · Tencent · Alibaba), Databricks Champion team, AI/Data/ML/Cloud,
regulated-industry work, NDA + IP clean, 2-week kickoff, 4-week pilot pod or staff-aug.

Two distinct motions that must never be mixed:
- `pitch_pod` — Avilex sells a pod to the company.
- `apply_personal` — Prem applies for the role himself, with his own resume.

**Why:** The pipeline stores `apply_mode` on every lead and `autopilot.send_queued_emails(mode=...)`
only sends leads whose stored `apply_mode` matches the requested mode. Sending a personal
application to a prospect who was pitched a pod (or vice versa) misrepresents the relationship.

**How to apply:** Default to `pitch_pod` for client outreach. Use `apply_personal` only when the
user explicitly asks for Prem to apply personally. Mention Prem by name and his experience only
when it directly supports the offer being made.
