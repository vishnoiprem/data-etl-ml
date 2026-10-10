---
lecture: L12
title: "Content Filtering — $.detail, $.detail-type, $.source, $.time"
duration: "9:30"
section: 3
prereqs: ["L11 (event pattern matching)"]
downloads:
  - "../../downloads/README.md"
---

# L12 — Content Filtering: `$.detail`, `$.detail-type`, `$.source`, `$.time`

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 3 — Rules + Event Patterns
> **Duration:** 9:30

## Prereqs

- L11 — the JSON predicate, exact match, AND over keys / OR inside arrays.

## Key terms

- **`source`** — the producer of the event. Conventionally a
  reverse-DNS string (`com.acme.orders`).
- **`detail-type`** — the verb / event name. Conventionally a
  human-readable PascalCase string (`Order Placed`).
- **`detail`** — the business payload. Free-form JSON.
- **`time`** — the timestamp the event was emitted, in ISO 8601.

## Lecture

Hi, I'm Prem Vishnoi. In L11 we covered the matching model: pattern
keys are AND, pattern values are OR. In this lecture we put that
model to work on the **four fields you'll filter on 95% of the
time**: `source`, `detail-type`, `detail.<field>`, and `time`.

### The four content fields

**`source` — who emitted the event**

Every event has a `source`. AWS services use a fixed namespace
(`aws.ec2`, `aws.s3`, `aws.dynamodb`); SaaS partner events use the
SaaS namespace (`zendesk`, `shopify`, `datadog`); your own events
should use a reverse-DNS string tied to your app:

```json
{ "source": ["my.app", "my.app.legacy"] }
```

**`detail-type` — what kind of event**

The `detail-type` is the verb. For AWS services it's the API call
name (`AWS API Call via CloudTrail`, `EC2 Instance State-change
Notification`); for your own events it's a PascalCase string:

```json
{ "detail-type": ["Order Placed", "Order Shipped", "Order Cancelled"] }
```

**`detail` — the business payload**

`detail` is a free-form JSON object. You constrain individual
fields inside it. The two most common patterns:

```json
// Single field
{ "detail": { "orderId": ["O-1001"] } }

// Multiple fields (ALL must match — this is an AND)
{ "detail": { "currency": ["USD"], "total": [129.99, 99.99] } }
```

**`time` — when the event happened**

`time` is the ISO 8601 timestamp. There are two useful filters:

```json
// Time-window filter — only fire between 09:00 and 17:00 UTC
{ "time": [{ "timestamp-between": ["2026-01-01T09:00:00Z", "2026-12-31T17:00:00Z"] }] }
```

The `timestamp-between` operator is one of a few **content-based
filtering** operators EventBridge supports inside arrays. The full
list is in the AWS docs; the ones you'll actually use are:
`exists`, `prefix`, `suffix`, `anything-but`, `numeric`, `cidr`,
`equals-ignore-case`, and `timestamp-between`.

### A real-world pattern: high-value order

Let's combine them. The rule: "Fire the high-value Lambda when an
order over $1000 USD is placed in the US store":

```json
{
  "source": ["my.app"],
  "detail-type": ["Order Placed"],
  "detail": {
    "store": ["us"],
    "currency": ["USD"],
    "total": [{ "numeric": [">=", 1000] }]
  }
}
```

That's **4 AND clauses**. Every event must satisfy all four. Note
the array inside `total` — the array holds a single object
`{"numeric": [">=", 1000]}` because `numeric` is itself an operator
that takes an array of arguments. We cover the operator forms in L13.

### Cross-field AND vs same-field OR

A common mistake is to write:

```json
{
  "detail": {
    "store": ["us"],
    "store": ["ca"]   // WRONG — duplicate key
  }
}
```

JSON objects don't have duplicate keys; the second `store` wins in
the parser and you only get `["ca"]`. The right way to OR over
**multiple values of the same field** is one array with multiple
elements:

```json
{ "detail": { "store": ["us", "ca", "mx"] } }
```

That's "store is one of `us`, `ca`, or `mx`". The AND is at the
top level (across keys), the OR is inside each value array.

### Why `detail-type` is more useful than `detail` for verbs

A common antipattern: putting the verb inside `detail`:

```json
// Antipattern
{ "detail": { "action": ["order_placed", "order_shipped"] } }
```

This works but you lose the ability to write a simple rule that
matches every "order" event across all states. By keeping the
verb in `detail-type`, you can:

```json
// Match every order verb
{ "source": ["my.app"], "detail-type": [{ "prefix": "Order " }] }
```

This is why the AWS spec promotes `detail-type` to a top-level
field. The convention is:

- **`source`** = the producer (a stable identifier)
- **`detail-type`** = the verb (a stable name, PascalCase)
- **`detail`** = the parameters (free-form)

### `resources` and `account` filters

Two envelope fields deserve a quick mention:

**`account` — which AWS account produced the event**

```json
{ "account": ["123456789012"] }
```

Useful for cross-account event patterns (L14).

**`resources` — ARNs of related AWS resources**

```json
{ "resources": ["arn:aws:s3:::my-bucket/*"] }
```

The `resources` field is an **array of strings** in the event, and
your pattern's value is also an array — the matching is per-element
inside the event array, not a substring search. (Use the `prefix`
operator from L13 for prefix matching on resources.)

### A note on $._ prefixed field paths

You may see patterns that use JSONPath-style syntax — e.g.
`$.detail.orderId`. EventBridge accepts that form too, but it's
**not required** — the shorthand `{ "detail": { "orderId": [...] } }`
is equivalent and easier to read. The `$` form is preserved in the
console for visual consistency; the wire format is the same.

## Hands-on

No separate demo for this lecture. After L15 you'll run the test
suite to see content filtering in action.

## Quiz prep

- What are the 4 most commonly filtered envelope fields? (`source`,
  `detail-type`, `detail.<field>`, `time`)
- How do you OR over multiple values of the same field? (Put them
  in a single array.)
- Where should the verb of an event go? (`detail-type`, not inside
  `detail`.)

## Further reading

- AWS docs: [Content-based filtering](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-filtering.html)
- [`./L13_prefix_wildcards.md`](./L13_prefix_wildcards.md) — next lecture

## What's next

L13 — **Prefix Matching + Wildcards + Arrays** — the operator forms
(`exists`, `numeric`, `prefix`, `anything-but`, `cidr`,
`equals-ignore-case`) that turn the event pattern from a strict
predicate into a flexible matching DSL.
