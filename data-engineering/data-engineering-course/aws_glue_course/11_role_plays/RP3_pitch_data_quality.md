# Role Play 3 — Pitch Glue Data Quality to a Skeptic Manager

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> **Pacing:** 10 minutes total
> **Personas:**
> - **Anika** (learner) — data engineer, owns the ingestion pipeline
> - **Daniel** (instructor / manager) — engineering manager, allergic to "shiny new tools"

## Scenario

Daniel: *"Anika, I saw your ticket about adding Glue Data Quality. I'm skeptical. Last time someone added a 'data quality' tool, it was a 6-month project and we got 2 alerts a quarter. Why do we need this? Convince me. And before you answer — what's the cost, both in dollars and in on-call time?"*

You have 10 minutes. The goal: get sign-off on a *pilot*, not a full rollout. Scope is the key.

## Learning objectives

1. Pitch Glue Data Quality in terms of **business risk**, not technical features.
2. Scope the pitch to a **pilot** with a measurable success criterion.
3. Address the **on-call tax** head-on — managers will ask.
4. Use the **3 concrete DQ rules** the course just covered (completeness, uniqueness, row-count match) — not the long tail of 30 rule types.

## Opening (60 seconds)

> **Anika:** "OK, let me start with the cost question, because that's the one that will kill the proposal if I don't answer it. There are 3 costs: the AWS bill for the DQ ruleset evaluation, the one-time engineering time to add the rules, and the recurring on-call. Let me give you a number for each."
>
> "DQ evaluation runs on the same Spark workers as the Glue Job. For our pipeline, it's a 5% increase in job runtime. At our current spend, that's about $40/month. The one-time work is 2 days of my time to write 3 rules — completeness on the `user_id` column, uniqueness on the `event_id` column, and a row-count check against the upstream. The on-call is the part I want to talk about, because you're right to flag it."

## The pitch (5 minutes)

> **Anika:** "Here's the business case. Last quarter we had 2 production incidents caused by upstream schema changes. One was a 4-hour outage on the marketing dashboard because a `null` in `campaign_id` broke a downstream ML model. The other was a 6-hour stale-data incident on the revenue dashboard because a producer started sending duplicate event_ids. Both of those are exactly the 3 rules I want to add. If the rules had been in place, both incidents would have been 15-minute CloudWatch alerts, not 4-hour and 6-hour outages."
>
> "I'm not proposing we add all 30 Glue DQ rule types. I'm proposing we add 3 — for the 2 pipelines that drove last quarter's incidents. The pilot scope is 2 pipelines, 3 rules, 4 weeks. Success criterion: zero incidents of the same root cause. If we get a fourth incident, the pilot failed and we rip the rules out."
>
> "On the on-call tax: yes, you'll get alerts. That's the point. The question is whether you want a 15-minute alert at 2am or a 4-hour outage at 9am. I can route the alerts to a low-priority SNS topic — same channel as our weekly log noise — and you only get paged if the alert is unacknowledged for 30 min. So on-call gets one page per quarter, not one per week."

## The ask (1 minute)

> **Anika:** "What I need from you: 2 days of my time this sprint, $50/month in AWS spend, and 30 minutes with you in 4 weeks to review whether the pilot worked. If yes, we expand. If no, we rip it out. The blast radius is bounded."

## What the role play tests

- **Quantitative pitch** — give a number for cost, time, and on-call. "It's cheap" is not an answer.
- **Scope discipline** — a pilot, not a rollout. 2 pipelines, 3 rules, 4 weeks.
- **Business framing** — incidents last quarter, dollar cost of downtime, not "DQ is a best practice."
- **On-call honesty** — acknowledge the tax, propose a mitigation (low-priority topic + 30-min escalation).

## Common mistakes learners make in this role play

- **Listing the 30 Glue DQ rule types.** The manager doesn't care. The 3 rules that map to last quarter's incidents are the only ones that matter for the pitch.
- **"Data quality is important"** without a number. "Important" is what the manager is skeptical of. "Last quarter cost us 10 engineering-hours in 2 incidents" is what they can budget against.
- **Pitching a full rollout.** Managers will reject a 6-month project. Pitch the 4-week pilot with a kill switch.
- **Not addressing the on-call tax.** Managers will ask. If you don't have an answer, you lose. The low-priority SNS topic + 30-min escalation is the standard answer.
- **Apologizing for the tool.** "I know it's a shiny new thing" is a self-inflicted wound. The tool is incidental — the business case is what matters.
