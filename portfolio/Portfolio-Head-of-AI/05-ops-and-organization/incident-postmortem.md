# Incident Postmortem

This document is what I'd put in front of a steering committee the
week after a real incident — the kind of postmortem that changes
behavior, not the kind that gets archived. It uses a placeholder
incident because the *shape* of the response is what I want the
reader to evaluate; the specifics will be different in any given
case.

The incident described here is the kind I have caused or watched:
a model drift that nobody caught for two weeks, an audit trail
that turned out to be incomplete, and a customer report that named
us by name.

## The incident (placeholder, realistic)

> **Date:** (a placeholder).
> **Severity:** P2.
> **Duration of user impact:** 11 days.
> **Title:** "Hallucinated policy citations in customer-facing summary emails."

### Summary

The fine-tuned adapter serving customer-facing summary emails began
generating paragraph fragments that cited specific policy numbers
(Section 7.b, in particular) that did not exist. The output was
formatted to look authoritative; recipients forwarded it onward as a
real citation. A customer escalation to compliance named the
specific outputs.

### Why we caught it late (11 days)

The drift detector (`agent/monitor.py`) reported a score that was
elevated but below the 0.3 threshold for two weeks. The threshold
was set when the underlying distribution was different. We had not
re-baselined it after a product-area change in week 3.

### Impact

- Three confirmed cases of policy citations that did not exist.
- An unknown number (≈50–250 est.) of unconfirmed cases across the
  11-day window; back-checking requires a sweep by compliance.
- A week of audit-trail recovery work; the run_id-stamped log
  format made the recovery possible.
- One customer filing a complaint with the regulator.

### Root causes

Listed in priority order — the order is the org change, not the
chronology:

1. **Drift threshold was set once and not revisited when the
   distribution legitimately changed.** A model-quality guard was
   treating a changed-product world as an unchanged-product world.
2. **The Tier-2 human-rated eval had drifted.** The 200-row
   refresh was supposed to land in Q3 pre-incident. It didn't, due
   to a rater-vendor slip that had been on the risk register for
   three weeks without escalation.
3. **The serving layer's adapter routing logs were sufficient for
   audit but not for *freshness* checks.** We could answer
   "which adapter served this?" but not "did the served adapter's
   revision hash match what we expected to be serving?"

### Contributing causes

- The serving engineer was on PTO for two of the eleven days.
  Bus-factor risk [R5 in `../04-delivery/risk-register.md`](./risk-register.md#the-12-risks-ill-defend).
- A model swap had not been followed by a full Tier-1 regression
  run; the regression suite was Tier-1 nightly but not on
  promotion. Promotion was gated only by the Tier-2 row count.

### What I did, in the 72 hours after

**Hour 0–6:** Freezed the serving layer. Pointed `@Champion` at
the previous adapter. Verified with two independent `chat.completions`
queries that the new output no longer contained the bad citation
form. Restored service with degraded throughput.

**Hour 6–24:** Pulled the run_id-stamped request log for the
11-day window. Built the list of downstream recipients by joining
with the email-send log. Worked with compliance on the sweep.

**Hour 24–72:** Wrote up the postmortem (this document); circulated
the working draft to the team and the steering committee.

## What I'd want from any serious incident

A real postmortem changes one of three things:

1. **A control.** Adding one that didn't exist, or tightening one
   that did.
2. **A process.** A documented sequence that someone will follow,
   not "be more careful."
3. **A surfacing rule.** A thing that was known but not raised, and
   the rule that prevents that happening again.

In this incident, all three changes happened. The control: drift
threshold re-baselined against the live distribution. The process:
Tier-2 evaluation is a hard promotion gate, on every adapter alias
change. The surfacing rule: a 1-week delay on a planned Tier-2 refresh
is now a P3 incident in its own right, not a project-management
detail.

Each change has an owner, a deadline, and a verifiable artifact.
Postmortem outputs that don't have all three of those don't ship to
the rest of the org.

## Things I will not do in a postmortem

| Out | Why |
|---|---|
| Assign blame to a person | Behavioral response to a system failure usually fixes one incident and prevents the org reporting the next one |
| List every contributing cause without a priority | The priority order *is* the postmortem; everything else is context |
| Promise zero re-occurrence | Unreal; train the team to detect future occurrences faster instead |
| Skip the surfacing rule | Most of the latent risk lives in things-that-were-known-but-not-raised |
| Hide the human-impact data | The customer's name is in this document; not because we want to shame ourselves, but because the cost is real |

The "I will not assign blame" line is the strongest of these. It is
the rule that, when held, makes the postmortem genuinely blameless
in the sense that matters: blameless enough that the next person
who notices a small thing raises it without fear.

## The two-hour rule

Within two hours of incident close, this document exists in
working draft. Two hours is a sharp bound but a deliberate one:

- Long enough that the team has had time to think.
- Short enough that the data — what was logged, who said what,
  what decision the steering committee made — is still retrievable.

After 24 hours, the meetings begin to drift; after a week, the
narrative solidifies into one of its many possible versions. Two
hours is when the postmortem is still cheap to write honestly.

## What this is in the artifact

This document is the flagship's "here is a thing that went wrong,
here is how it was handled, here is what we changed" entry. It is
also the *reason* the entire rest of the doc exists:

- The cost-model splits that the budget exists.
- The risk register names what we see coming.
- The org design explains who saw it.
- The eval strategy is what defines "the model is wrong."

If a single one of those had not been in place when this incident
hit, the response would have been an order of magnitude worse. The
incident reads as a system failing locally because the system was
not built yet. The rest of this document is the system being built.

## The rule I hold

> Postmortems earn their existence by changing one control, one
> process, or one surfacing rule. Without one of those changes, the
> postmortem is a document for the archive, and the next incident
> is closer than the calendar says.