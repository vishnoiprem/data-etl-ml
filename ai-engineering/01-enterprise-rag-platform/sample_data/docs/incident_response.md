# Incident Response Runbook (Sev 1 / Sev 2)

## Overview

This runbook governs production incidents at severity 1 and 2. It defines
roles, communication cadence, and the post-incident process.

## Severity definitions

- **Sev 1** — Customer-facing outage of a tier-0 service, OR confirmed data
  exposure. Page everyone, all the time.
- **Sev 2** — Significant degradation, partial outage, or single-tenant
  impact on tier-0/1.
- **Sev 3** — Single-customer or non-customer-facing issue.

## Roles

- **Incident Commander (IC)** — owns the incident end-to-end. Decides actions
  and arbitrates. Not necessarily the most senior engineer.
- **Communications Lead** — owns the status page, internal Slack updates,
  customer comms.
- **Scribe** — records the timeline in real time.
- **Subject Matter Experts (SMEs)** — engineers from the affected services.

## Declaration

Any engineer may declare a Sev 1 or Sev 2. Declare via `/incident declare`
in Slack. The bot pages the on-call IC, opens the war room, and creates the
status page draft.

## During the incident

- Updates every 30 minutes minimum (Sev 1) or 60 minutes (Sev 2).
- Customer comms on the status page within 15 minutes (Sev 1).
- Major decisions go in the war-room channel, not DMs.

## Resolution

The IC declares resolution. Resolution requires:
- Customer impact has ended.
- Monitors are green for 30 minutes.
- A holding fix is in place even if the root cause is not yet resolved.

## Post-incident

- Within 24 hours: a post-incident review (PIR) is scheduled.
- Within 5 business days: PIR is held; the IC presents the timeline,
  contributing factors, and a list of action items.
- Within 30 days: action items are tracked to closure or formally accepted
  with a residual-risk justification.

PIRs are blameless. We focus on systems and processes, not individuals.
