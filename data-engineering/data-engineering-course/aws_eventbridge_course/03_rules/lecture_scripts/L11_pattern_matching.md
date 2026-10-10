---
lecture: L11
title: "Event Pattern Matching — The JSON Predicate"
duration: "10:45"
section: 3
prereqs: ["L10 (rules 101)"]
downloads:
  - "../../downloads/README.md"
---

# L11 — Event Pattern Matching: The JSON Predicate

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 3 — Rules + Event Patterns
> **Duration:** 10:45

## Prereqs

- L10 — what a rule is, ENABLED vs DISABLED, role assumption.

## Key terms

- **Event** — a JSON object with a fixed envelope (`version`,
  `id`, `source`, `account`, `time`, `region`, `resources`,
  `detail-type`, `detail`). The schema is documented in the EventBridge
  spec.
- **Predicate** — a JSON document you write that evaluates to
  `true` or `false` against a given event.
- **Exact match** — the default matching mode. `"source": "my.app"`
  matches only if the event's `source` field is *exactly*
  `"my.app"`.
- **OR over arrays** — when a pattern field is a JSON array, the
  event matches if **any** element equals the event's value. This is
  the most useful thing about event patterns.

## Lecture

Hi, I'm Prem Vishnoi. Welcome back. In L10 you learned that a rule
has two responsibilities — filter and route. In this lecture we go
**deep on the filter** part. The filter is a JSON document called
the **event pattern** and it's the single most important thing
you'll write when working with EventBridge. Get this right and
your pipeline works. Get it wrong and either nothing fires or
everything fires and you spend three days debugging.

### What an event looks like

Every event on EventBridge has a fixed **envelope**. The
`detail-type` and `detail` fields are payload; the rest is metadata:

```json
{
  "version": "0",
  "id": "abcd-1234-...",
  "detail-type": "Order Placed",
  "source": "my.app",
  "account": "123456789012",
  "time": "2026-10-10T12:00:00Z",
  "region": "us-east-1",
  "resources": ["arn:aws:..."],
  "detail": {
    "orderId": "O-1001",
    "total": 129.99,
    "currency": "USD"
  }
}
```

The envelope is the same for **all** events — yours, AWS services',
and SaaS partner events. The only thing that changes is the `detail`
payload.

### The simplest event pattern

A pattern is a JSON object. Each **key** in the pattern is matched
against a key in the event. Each **value** is the constraint:

```json
{
  "source": ["my.app"]
}
```

This pattern says: "Match any event whose `source` field is in the
array `["my.app"]`." Since `"my.app"` is the only element, it
matches events where `source == "my.app"`. The **array** is the OR
clause — and the most common mistake is forgetting it.

Compare:

```json
{ "source": "my.app" }       // INVALID — values must be arrays (or matching objects)
{ "source": ["my.app"] }     // valid — matches source == "my.app"
{ "source": ["my.app", "my.legacy"] }  // valid — matches either
```

(Technically, a scalar value is accepted in some positions, but the
**safe, recommended** form is always an array. We always use
arrays in this course.)

### Exact-match semantics

The default is **exact match**. The pattern `"orderId": ["O-1001"]`
matches only if the event's `detail.orderId` is **exactly**
`"O-1001"`. If the event has `detail.orderId = "o-1001"` (lowercase
o) the pattern does **not** match. Case-sensitive, no normalization,
no trimming.

```json
// Event detail
{ "orderId": "O-1001" }

// Pattern — matches
{ "detail": { "orderId": ["O-1001"] } }

// Pattern — does NOT match (lowercase o)
{ "detail": { "orderId": ["o-1001"] } }
```

### How matching is evaluated

EventBridge evaluates a pattern by walking the pattern key by key.
For each key, it checks the corresponding field in the event:

1. If the event has the field, the value must satisfy the pattern
   value. For scalar patterns, the event value must be in the array.
2. If the event **does not** have the field, the pattern **fails**
   for that key (unless you use `exists`, which we cover in L13).
3. All keys in the pattern must satisfy their constraints. If any
   one fails, the entire event is dropped.

So an event pattern is a logical **AND** over its top-level keys,
with an **OR** inside each value array. That's the entire mental
model.

```json
// source MUST be "my.app"
// AND detail-type MUST be "Order Placed"
{
  "source": ["my.app"],
  "detail-type": ["Order Placed"]
}
```

### Patterns are a subset of the event

A pattern doesn't have to enumerate every field of the event. It
only needs to constrain the fields you care about. The event:

```json
{
  "source": "my.app",
  "detail-type": "Order Placed",
  "time": "2026-10-10T12:00:00Z",
  "detail": { "orderId": "O-1001", "total": 129.99 }
}
```

matches the simple pattern:

```json
{ "source": ["my.app"] }
```

because the pattern only constrains `source` and the event satisfies
that constraint. The other event fields are ignored.

### Top-level vs nested fields

For envelope fields (`source`, `detail-type`, `time`, `account`,
`region`, `resources`, `id`, `version`) the pattern uses the
**envelope key directly**:

```json
{ "source": ["my.app"], "detail-type": ["Order Placed"] }
```

For `detail` fields you have two options. The **shorthand** is
`detail.<field>`, and the **longhand** is a nested `detail` object:

```json
// Shorthand (recommended for one field)
{ "detail": { "orderId": ["O-1001"] } }

// Longhand (use for multiple detail fields)
{ "detail": { "orderId": ["O-1001"], "total": [129.99] } }
```

Both are valid; the shorthand is what the console shows by default.

### A worked example

Event:

```json
{
  "source": "my.app",
  "detail-type": "Order Placed",
  "time": "2026-10-10T12:00:00Z",
  "detail": { "orderId": "O-1001", "total": 129.99 }
}
```

Patterns and matches:

| Pattern | Matches? | Why |
|---|---|---|
| `{ "source": ["my.app"] }` | yes | `source == "my.app"` |
| `{ "source": ["other.app"] }` | no | `source != "other.app"` |
| `{ "source": ["my.app"], "detail-type": ["Order Placed"] }` | yes | both constraints satisfied |
| `{ "source": ["my.app"], "detail-type": ["Order Shipped"] }` | no | `detail-type` fails |
| `{ "detail": { "orderId": ["O-1001"] } }` | yes | nested constraint satisfied |
| `{ "detail": { "orderId": ["O-1002"] } }` | no | `orderId` doesn't match |

That's the entire matching model. L12 adds the content-filtering
syntax; L13 adds prefix/wildcard/array forms.

## Hands-on

For this lecture there is no separate demo — the matching rules
themselves are tested in the `test_put_rule.py` suite we cover in
L15.

```bash
# Preview (after L15)
python3 -m pytest 03_rules/code/test_put_rule.py -v -k pattern
```

## Quiz prep

- What does an array value mean in a pattern? (OR — match if any
  element equals the event value)
- Is the default matching exact or fuzzy? (Exact)
- Is matching case-sensitive? (Yes)
- What happens if a pattern key is missing from the event?
  (Pattern fails for that key, unless you use `exists`)

## Further reading

- AWS docs: [EventBridge event patterns](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html)
- AWS docs: [EventBridge event content](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-events.html)
- [`./L12_content_filtering.md`](./L12_content_filtering.md) — next lecture

## What's next

L12 — **Content Filtering (`$.detail`, `$.detail-type`, `$.source`,
`$.time`)** — we look at the specific fields you'll filter on most
often: `source` (the producer), `detail-type` (the verb),
`detail.<field>` (the business payload), and `time` (for time-window
filters).
