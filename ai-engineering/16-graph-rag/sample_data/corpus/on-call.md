# On-Call Rotation

The on-call rotation is a weekly rotation across the engineering team.

## Schedule

- **Shift length**: 7 days, Monday 10:00 → following Monday 10:00 (local time).
- **Primary + secondary** every shift. The secondary is paged if the primary
  does not acknowledge within 5 minutes.
- The rotation is published in PagerDuty and visible in #oncall-eng.

## §2. Incident Severity

Incidents are graded SEV1 to SEV4:

- **SEV1** — total outage or data loss. Page within 5 min, war room.
- **SEV2** — major degradation. Page within 5 min, incident channel.
- **SEV3** — partial degradation. Business-hours page.
- **SEV4** — minor / cosmetic. Ticket-only, no page.

## §3. Handoff

At the end of each shift, the outgoing on-call writes a short handoff note
in #oncall-eng: anything in progress, anything to watch, any followups.

## §4. Compensation

On-call pay is **$250/week** for the primary rotation, $125/week for
secondary. Incidents responded to outside business hours earn additional
flat-rate comp-time per the engineering handbook.
