---
lecture: L26
title: "Filter Pattern Syntax — exact, json, space-delimited tokens"
duration: "10:00"
section: 6
prereqs: ["L25"]
---

# L26 — Filter Pattern Syntax — exact, json, space-delimited tokens

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 6 — Logs Insights + Subscriptions
> **Duration:** 10:00

## Prereqs

L25 (subscription filters 101).

## Key terms

- **Plain-text pattern** — match the substring anywhere in the log
  event. `"ERROR"` matches any event with `ERROR` somewhere in the
  message.
- **JSON pattern** — `{ $.field = "value" }` matches a specific JSON
  field.
- **Space-delimited tokens** — `?ERROR ?WARN` matches an event that has
  *both* `ERROR` and `WARN` somewhere.
- **Negation** — `-DEBUG` excludes events containing `DEBUG`.
- **Match against AWS service metric filters** — a separate "metric
  filter" syntax is **the same**; both go through the same parser.

## Lecture

The filter pattern syntax is *not* a regex. It's a small DSL that
covers 95% of cases. Three forms:

### 1. Plain text (substring match)

```python
filterPattern="ERROR"
```

Matches any event whose `message` contains `ERROR`. (Case-sensitive.)

### 2. JSON match

```python
filterPattern='{ $.level = "ERROR" }'
filterPattern='{ $.status >= 500 }'
filterPattern='{ $.user_id = 42 && $.path = "/checkout" }'
```

JSON match uses JSONPath (`$`, `$.field`, `$.field.subfield`).
Operators: `=`, `!=`, `>=`, `<=`, `>`, `<`, `&&`, `||`.

> **Note:** `=` is the equality operator, not `==`. This trips up
> half the developers who use it for the first time.

### 3. Space-delimited tokens (AND across substrings)

```python
filterPattern="?ERROR ?WARN"     # ERROR AND WARN
filterPattern="?ERROR -DEBUG"    # ERROR AND NOT DEBUG
```

Each token is matched as a substring; the leading `?` and `-` give
AND / NOT semantics.

### Common patterns

| Pattern | Matches |
|---|---|
| `ERROR` | any event containing `ERROR` |
| `-DEBUG` | any event **not** containing `DEBUG` |
| `?ERROR ?Timeout` | events with both `ERROR` and `Timeout` |
| `{ $.level = "ERROR" }` | JSON events with `level=ERROR` |
| `{ $.status >= 500 && $.status < 600 }` | 5xx responses |
| `{ $.user_id = 42 }` | events for a specific user |
| `{ $.path = "/checkout" }` | checkout endpoint events |

### What's *not* supported

- No regex (`.*`, `\d+`, character classes, etc.).
- No `OR` for plain-text; only AND.
- No lookbehind / lookahead.

For complex matching, **use Logs Insights** queries inside a *metric
filter* (you can do regex via `parse` in metric filter syntax — see
the CloudWatch docs).

### Using the syntax in both filters

- **Subscription filter** — selects events to *forward* to a
  destination.
- **Metric filter** — counts events that match; turns them into a
  CloudWatch metric. Same syntax.

## Hands-on

In your AWS account, try these filter patterns against a Lambda
log group with some test events:

1. `ERROR` — should match the error event.
2. `{ $.level = "ERROR" }` — same, but JSON-aware.
3. `?ERROR ?Timeout` — only the event that has *both* substrings.

Use the console: *Logs → Insights* (you can dry-run a filter pattern
in the Insights editor with `filter`).

## Quiz prep

- What's the equality operator in a JSON filter? (`=`, not `==`.)
- How do you write "ERROR but not DEBUG"? (`?ERROR -DEBUG`.)
- Is regex supported? (No — use Logs Insights for regex.)

## Further reading

- `https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html`

## What's next

L27 — Kinesis Data Streams + Firehose as Destinations.
