# Section 2 — EventBus Basics

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Lectures:** L05–L09
> **Duration:** ~33 min

This section turns the conceptual vocabulary from section 1 into real
AWS objects. We open with **what an event bus is** — a logical
router that is both **regional** and **account-scoped**. We then
look at the three kinds of bus you can have: the **default bus**
(auto-created, undeletable), **custom buses** (you create them with
`CreateEventBus`), and **partner buses** (for SaaS events, name
prefix `aws.partner/`). We close with the **resource policy** model
that controls *who* can publish to a bus.

By the end of this section you should be able to create and inspect
event buses with boto3, attach a cross-account resource policy, and explain
when you'd reach for a custom bus instead of the default.

| L# | Title | Min |
|---|---|---|
| L05 | What is an Event Bus? | 6:00 |
| L06 | The Default Event Bus | 5:30 |
| L07 | Custom Event Buses | 6:00 |
| L08 | Partner Event Bus (SaaS events) | 7:00 |
| L09 | Section Recap + `create_event_bus.py` + tests | 8:00 |

## What the demo does

`02_eventbus_basics/code/create_event_bus.py` is the first of the
course's five working demos. It:

1. **Creates a custom bus** named `acme-orders` (override with
   `--name`). If the bus already exists, it catches
   `ResourceAlreadyExistsException` and continues — that's the
   idempotency.
2. **Attaches a resource policy** granting a specified source account
   the right to call `events:PutEvents` on the bus.
3. **Lists every bus** in the (account, region) and prints its name
   and ARN.
4. Has a **`--dry-run`** flag that short-circuits before any boto3
   call, suitable for CI sanity checks.

The accompanying `test_create_event_bus.py` has **9 moto tests**
that prove: create-once works, re-create is a no-op, the resource
policy is attached with the right principal and action, our bus
appears in the list, dry-run makes zero AWS calls (verified by
patching `boto3.client` with `MagicMock`), delete removes the bus,
and an unrelated `ClientError` propagates instead of being swallowed.

Run them from the course root:

```bash
python3 -m pytest 02_eventbus_basics/code/test_create_event_bus.py -v
```

Expected: **9 passed** in under 2 seconds, no AWS calls.

## Key concepts you'll need later

- **Default bus** = `default`, undeletable, receives AWS service
  events.
- **Custom bus** = one you created with `CreateEventBus`. Used for
  isolation and cross-account sharing.
- **Partner bus** = `aws.partner/<vendor>`, auto-created when you
  associate with a SaaS partner.
- **Resource policy** = JSON policy attached to a bus that says who
  can call `PutEvents` on it.
- **Idempotent script** = one you can run any number of times and
  the end state is the same.

## What comes next

Section 3 is **Rules + Event Patterns** — the matching logic that
decides which events on a bus trigger which targets. We introduce
the JSON-predicate event pattern language and write the
`put_rule.py` demo.