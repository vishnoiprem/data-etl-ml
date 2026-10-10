# Lesson 32 — Design a Data Warehouse Schema for Customer Support

> **Format:** mock interview transcript (~30 minutes).
> Read it aloud. Note the *state-machine modeling* on
> tickets and the *multi-channel attribution* problem.

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;

---

## Why this lesson

A customer support warehouse is a great system-design
round because it sits at the intersection of three
classic interview themes: a *rich state machine*
(new → open → pending → solved → closed), *event
streams at high volume* (every email reply, every chat
turn, every phone note is an event), and *cross-channel
attribution* (one customer problem might arrive via
Twitter, escalate through email, and resolve on a
phone call). The interviewer is testing whether you
can model the *state*, not just the *headline* ticket
row. Strong candidates walk in knowing that
`fact_ticket_events` (not `fact_tickets`) is the grain
that powers SLA dashboards, and that CSAT must be
modeled as its own fact because the survey is a
*separate* workflow from the ticket.

---

## The prompt

> Design a data warehouse for a customer support
> platform (think Zendesk, Intercom, or Front). We
> have 10M tickets, 50M ticket events, 5000 agents,
> across email, chat, phone, and social. Support
> managers need dashboards on SLA compliance, agent
> productivity, ticket resolution time, CSAT, and
> channel performance.

---

## Step 1: Requirements gathering

A senior candidate asks five questions before
drawing anything:

1. **What is a "ticket"?** A ticket has a creation
   event, a status timeline, an assignee, a requester,
   and (often) a conversation thread. I want to confirm
   the grain of the headline fact — one row per
   *ticket* or one row per *ticket event*?
2. **What is the SLA?** Is it first-response-time
   (FRT) — time from ticket creation to first agent
   reply — or full-resolution-time (FRT-to-resolution)?
   And is the SLA target a function of priority
   (P1 = 1h, P2 = 8h, P3 = 24h)?
3. **What channels?** Email, chat, phone, social
   (Twitter, Facebook, Instagram DM). Does one ticket
   span multiple channels — i.e., a customer tweets,
   then the agent replies by email — and we need to
   attribute the resolution to the *first* channel or
   the *last* channel?
4. **What is CSAT?** A 1-to-5 survey sent after
   resolution. Is the response attached to the ticket,
   to the agent, or to the channel? I assume ticket-
   level, with a 30% response rate.
5. **Are agents organized into teams?** Tier 1 / Tier
   2 / Tier 3, with escalation paths? And do we need
   shift-level granularity (an agent is "on shift"
   during certain hours)?

---

## Step 2: High-level architecture

Two fact tables at the heart of the warehouse:

```mermaid
fact_ticket_events   (grain: 1 row per event)
   ├── ticket_key        → dim_ticket
   ├── agent_key         → dim_agent
   ├── customer_key      → dim_customer
   ├── channel_key       → dim_channel
   ├── event_type_key    → dim_event_type
   ├── event_date_key    → dim_date
   ├── event_time_key    → dim_time
   ├── event_ts          (TIMESTAMP, degenerate)
   ├── is_sla_breach     (BOOLEAN)
   ├── response_seconds  (INT, NULL if not a reply)
   └── text_chars        (INT — for response-length KPI)

fact_agent_activity  (grain: 1 row per (agent, day))
   ├── agent_key         → dim_agent
   ├── date_key          → dim_date
   ├── tickets_touched   (INT)
   ├── tickets_resolved  (INT)
   ├── replies_sent      (INT)
   ├── chats_handled     (INT)
   ├── calls_handled     (INT)
   ├── avg_handle_secs   (INT)
   └── csat_avg          (REAL — agent-rolling 7-day)
```

Dimensions (all conformed across the two facts):

- `dim_ticket` — SCD 1. ticket_id, subject, product,
  category, subcategory, priority, status (current
  only — full history is in fact_ticket_events),
  created_at, resolved_at, requester_key.
- `dim_agent` — SCD 2. agent_id, name, team, tier,
  shift_start, shift_end, hire_date, is_active.
- `dim_customer` — SCD 2. customer_id, name, plan,
  signup_date, country, language, is_trial.
- `dim_channel` — small dim. email, chat, phone,
  twitter, facebook, instagram_dm.
- `dim_event_type` — small dim. created, assigned,
  replied, internal_note, status_changed, resolved,
  reopened, escalated, closed.
- `dim_date` — conformed. role-played on every *_date_key.
- `dim_time` — separate from date; one row per minute.
  Role-played for event timestamps.

There is a third fact, less often drawn but essential:
`fact_csat_surveys` — grain of one row per survey
*response*. The "fact" is that the customer answered
the survey. Measures: `rating` (1–5), `response_lag_hours`.
Dimensions: `dim_ticket`, `dim_agent`, `dim_channel`,
`dim_date`. The fact joins back to the ticket on
`ticket_id`. CSAT is computed as `AVG(rating)` over a
date range, joined to agent or channel for slicing.

---

## Step 3: The 3 hardest parts

### 3.1 The ticket state machine

A ticket is not a row — it is a *trail of events*.
`status` is not an attribute of the ticket, it is the
*result* of the most recent `status_changed` event.
This is the single most common modeling error in
support warehouses: storing `status` as an SCD 1
column on `dim_ticket` and overwriting it on every
change. That destroys the audit trail, breaks SLA
reports ("was this ticket ever P1?"), and makes it
impossible to answer "how long did this ticket spend
in `pending_customer` status?"

The correct model is `fact_ticket_events` with an
`event_type_key` for `status_changed`, carrying the
`from_status` and `to_status` as measures on the
event row. To compute "current status," the analyst
joins the ticket to its most recent status-changed
event using a window function:

```sql
SELECT t.ticket_id,
       e.to_status AS current_status
FROM dim_ticket t
JOIN LATERAL (
  SELECT to_status
  FROM fact_ticket_events
  WHERE ticket_key = t.ticket_key
    AND event_type_key = (SELECT event_type_key
                          FROM dim_event_type
                          WHERE event_type_name = 'status_changed')
  ORDER BY event_ts DESC
  LIMIT 1
) e;
```

The same pattern answers "how long was this ticket
in `pending_customer`?" — sum the durations between
status-changed events. That is a window function over
`fact_ticket_events` grouped by ticket and ordered by
`event_ts`.

### 3.2 Resolution time calculation

"Resolution time" has three definitions:

1. **First-response time (FRT)** — ticket creation to
   first agent reply. *One event per ticket.*
2. **Full-resolution time (FRT-to-resolution)** —
   ticket creation to the first `resolved` event.
   *One event per ticket.*
3. **Handle time** — sum of all `is_agent_reply`
   events' `response_seconds`. Multiple events.

FRT is the SLA the manager cares about, but only for
*priority* P1/P2. The query:

```sql
SELECT t.priority,
       AVG(JULIANDAY(first_reply.event_ts) -
           JULIANDAY(t.created_at)) * 86400
       AS avg_first_response_secs
FROM dim_ticket t
JOIN LATERAL (
  SELECT event_ts
  FROM fact_ticket_events e
  JOIN dim_event_type et ON e.event_type_key = et.event_type_key
  WHERE e.ticket_key = t.ticket_key
    AND et.event_type_name = 'replied'
  ORDER BY event_ts ASC
  LIMIT 1
) first_reply;
```

This is a *correlated lateral* — slow on a large fact.
In production, pre-aggregate: `fact_first_response`
at the grain of one row per ticket, with
`first_reply_ts` and `first_response_secs` already
materialized at ETL time. The OLAP query then
filters and groups on a much smaller fact.

### 3.3 Multi-channel attribution

One customer problem, multiple channels: a tweet
creates a ticket, the agent replies by email, the
customer calls to follow up, the agent resolves on
the call. Which channel "owns" the resolution?

Two models:

- **First-touch attribution** — credit the channel of
  the ticket-creation event. Easy, but Twitter is
  over-credited (Twitter is loud, not the actual
  problem channel).
- **Last-touch attribution** — credit the channel of
  the resolution event. Easy, but Twitter is
  under-credited.
- **Multi-touch** — split credit across all channels
  the ticket touched. Most accurate, hardest to
  compute, and rarely needed in a first-pass
  warehouse.

For a first-pass support warehouse, use **last-touch
on resolution**. Add `attributed_channel_key` to a
small `fact_resolutions` denormalized table that the
manager's dashboard reads. The ETL picks the channel
of the most recent event with `event_type = resolved`
on that ticket.

---

## Step 4: Common failure modes

1. **Storing `status` on `dim_ticket`.** Destroys the
   audit trail. The state machine lives in
   `fact_ticket_events`; `dim_ticket` holds only
   "currently visible" attributes (subject,
   priority, requester).
2. **One row per ticket instead of one row per
   event.** The "ticket" grain answers "how many
   tickets today?" but not "how many replies did
   the agent send today?" or "what was the
   first-response time?" Always pick the *finest*
   grain that has the measures the analyst needs —
   usually events.
3. **Float for response time.** Use `INTEGER` seconds
   (or `BIGINT` milliseconds). Float introduces
   rounding errors that compound over millions of
   events.
4. **No dim for event type.** The "type" of event
   is a low-cardinality descriptor (created,
   replied, resolved, etc.) — it earns its own dim
   because the analyst filters by it constantly.
5. **Forgetting CSAT.** The CSAT survey is a
   *separate* workflow that joins to the ticket on
   `ticket_id`. It is a third fact, not a measure on
   `dim_ticket`. Candidates who stuff CSAT onto the
   ticket dim lose the ability to track response
   rate, lag, and per-channel CSAT.

---

## Step 5: Scoring against the rubric

| Bucket | Score | Notes |
|---|---|---|
| **Clarifies the business** | 5/5 | Asked about ticket vs event grain, SLA definition, channel attribution, CSAT workflow, team hierarchy. |
| **Picks a grain** | 5/5 | `fact_ticket_events` (events), `fact_agent_activity` (agent × day), `fact_csat_surveys` (response). Defended each. |
| **Makes and defends tradeoffs** | 5/5 | State machine in events not dim, FRT pre-aggregated, multi-touch attribution deferred. |
| **Talks while drawing** | 5/5 | Narrated every dim, every FK, every measure. |

---

## In the interview, you would say...

> "The central fact is `fact_ticket_events`, not
> `fact_tickets`. A ticket is a *trail of events*; the
> status, the assignee, and the resolution time are
> all derivable from the event stream, not stored on
> the ticket. SLA is computed as the lag from
> `created` to the first `replied` event, and we
> pre-aggregate that into a `fact_first_response` so
> the dashboard query reads from a 10M-row fact
> instead of a 50M-row one. CSAT is a separate fact
> because the survey is a different workflow with
> its own response-rate dynamics — stuffing it onto
> the ticket dim would lose that."

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
