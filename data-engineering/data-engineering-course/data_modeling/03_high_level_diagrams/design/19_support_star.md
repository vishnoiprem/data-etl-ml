# Lesson 19 — Designing a Star Schema for Customer Support

> **What you'll learn:** the customer-support star, with a
> ticket-event fact, an agent dim, and a channel dim. By the
> end of this lesson you'll be able to draw a support
> warehouse for Zendesk, Intercom, or any help-desk product.

---

## The prompt

> "Design a data warehouse for a customer support product so
> the operations team can answer questions about ticket
> volume, agent performance, and resolution time."

This is the fourth canonical question. The expected schema is
a ticket-event fact at the event grain, with `dim_tickets`,
`dim_customers`, `dim_agents`, and `dim_date`.

---

## The star schema

```
                ┌──────────────┐
                │ dim_customers│
                │ (SCD 2)      │
                └──────┬───────┘
                       │ customer_key
                       ▼
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│ dim_date │◄───┤ fact_ticket_ ├───►│ dim_tickets  │
└──────────┘    │   events     │    └──────────────┘
                │              │
                │ measures:    │    ┌──────────────┐
                │  minutes_    │◄───┤ dim_agents   │
                │   since_open │    │              │
                └──────────────┘    └──────────────┘
                       │
                       ▼
                ┌──────────────┐
                │dim_event_type│
                └──────────────┘
```

Six tables. One fact, five dimensions.

---

## Why an event-grain fact

Support tickets have a *lifecycle*: opened → assigned →
responded → (maybe escalated) → resolved. Each step is an
event. To answer "how long does it take to resolve a
ticket on average?" we need the opened and resolved events.
To answer "how many tickets got escalated this month?" we
need the escalated events.

Two schema choices:

1. **Ticket-level snapshot** — one row per ticket, with
   columns for `opened_at`, `assigned_at`, `first_response_at`,
   `resolved_at`. The row is mutated as the ticket moves
   through its lifecycle.
2. **Event-grain fact** — one row per event, with a
   `minutes_since_open` measure. The ticket never mutates;
   new events are appended.

The event-grain fact is the right choice for two reasons:

- **Auditability.** Every state change is recorded. The
  ticket-level snapshot loses the *path* through the
  lifecycle.
- **Flexibility.** A new event type (e.g., "reopened")
  doesn't require a schema change. With the snapshot, you'd
  have to add a new column.

The trade-off: the event-grain fact has more rows. For a
typical support volume (10k tickets/day, 3–5 events each),
that's 30k–50k rows/day. Fine.

---

## The measures

The only numeric measure is `minutes_since_open` — the time
between the ticket being opened and the current event. This
is what makes the schema useful: every event has a
"how-late-is-this?" number, and the analyst can compute
"average time to first response" or "time to resolution"
by grouping.

`event_type_key` is a categorical measure (a low-cardinality
column on the fact). It points to `dim_event_type` so the
analyst can attach attributes like `is_terminal` or
`is_responded`.

---

## The dimensions

### `dim_tickets`

A ticket has a `subject`, `category` (bug, account,
billing), `priority`, and `channel` (email, chat, in-app).
Most of these are static once the ticket is created. SCD 1
is fine — overwrite if the user changes the priority or
the agent re-categorizes the ticket.

### `dim_customers` (SCD Type 2)

The customer's `plan` (free, pro, enterprise) changes over
time. We need historical attribution: "what plan was this
customer on when they opened this ticket?" SCD 2.

### `dim_agents`

An agent has a name, a team (tier1, tier2, billing), and
(less commonly) a tenure. SCD 1 is usually fine.

### `dim_date`

The standard conformed dim. Add `month` and `quarter` for
executive reporting.

### `dim_event_type`

A small dim with 5 rows: opened, assigned, responded,
escalated, resolved. The attributes let the analyst
filter for "is this a terminal event?" or "is this a
response event?".

---

## The role of `dim_tickets`

`dim_tickets` is interesting because it's a *non-time-varying*
dim that nonetheless needs a primary key. We use a synthetic
`ticket_key` (surrogate) so the fact table can FK to it
without leaking the OLTP `ticket_id`.

The relationship between the fact and `dim_tickets` is
many-to-one: many events per ticket. A single ticket
generates 4–5 events in its lifetime.

The relationship between the fact and `dim_customers` is
also many-to-one, but with a subtle twist: the customer's
SCD 2 row at the time of the event is the one we want.
That requires a temporal join: the fact's `date_key` must
fall within the dim's `[effective_date, expiry_date)`
range. We cover the temporal join in Lesson 21.

---

## Tradeoffs to call out

1. **Why event-grain, not ticket snapshot?** "The
   lifecycle is the point. A snapshot loses the path; an
   event-grain fact keeps every state change."
2. **Why `dim_tickets` SCD 1, not SCD 2?** "Ticket
   attributes are mostly static after creation. Priority
   and category changes are rare and don't usually need
   historical attribution."
3. **Why a separate `dim_event_type`?** "So we can attach
   attributes to event types (e.g., `is_terminal`,
   `is_responded`). A TEXT column on the fact loses this."
4. **Why `dim_agents` SCD 1?** "Agent attributes (name,
   team) are mostly static. Tenure could be SCD 2 if the
   analytics team needs 'agent performance by year of
   tenure'."
5. **Why not denormalize customer plan onto the ticket?**
   "The customer's plan at the time of the event is what
   we want. Denormalizing it onto the ticket would be
   wrong (the plan can change mid-ticket-resolution)."

---

## The DDL — running it

The full DDL is in
[`code/star_schemas.py`](../code/star_schemas.py) as
`build_support_schema(q)`. Run the demo:

```bash
python3 data_modeling/03_high_level_diagrams/code/star_schemas.py
```

Output (truncated):

```
[support]  tables: ['dim_customers', 'dim_tickets', 'dim_agents',
                    'dim_event_type', 'dim_date', 'fact_ticket_events']
   fact_ticket_events sample row: {
     'event_key': 1, 'ticket_key': 1, 'customer_key': 1,
     'agent_key': 1, 'event_type_key': 1, 'date_key': 20240401,
     'minutes_since_open': 0
   }
```

---

## Sample queries

### Average time to first response

```sql
SELECT
    AVG(minutes_since_open) AS avg_min_to_first_response
FROM fact_ticket_events f
JOIN dim_event_type et ON f.event_type_key = et.event_type_key
WHERE et.event_type = 'responded';
```

### Tickets escalated by team

```sql
SELECT
    a.team,
    COUNT(*) AS escalations
FROM fact_ticket_events f
JOIN dim_event_type et ON f.event_type_key = et.event_type_key
JOIN dim_agents a ON f.agent_key = a.agent_key
WHERE et.event_type = 'escalated'
GROUP BY a.team
ORDER BY escalations DESC;
```

### Resolution time by plan

```sql
SELECT
    c.plan,
    AVG(
        CASE WHEN et.event_type = 'resolved'
             THEN f.minutes_since_open END
    ) AS avg_minutes_to_resolve
FROM fact_ticket_events f
JOIN dim_event_type et ON f.event_type_key = et.event_type_key
JOIN dim_customers c ON f.customer_key = c.customer_key
WHERE c.is_current = 1
GROUP BY c.plan
ORDER BY avg_minutes_to_resolve;
```

(Note: the `is_current = 1` filter pins the customer to
their *current* SCD 2 version. For historical analysis,
drop the filter and add a temporal join. We cover this
in Lesson 21.)

---

## Try it

Open
[`code/star_schemas.py`](../code/star_schemas.py) and read
`build_support_schema`. Then:

1. State the grain out loud: "one row per ticket event."
2. Identify why the fact needs `agent_key` *and*
   `customer_key` (the agent who did the action, the
   customer the action was for).
3. Run the test:

```bash
python3 -m unittest data_modeling/03_high_level_diagrams/tests/test_schemas.py
```

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
