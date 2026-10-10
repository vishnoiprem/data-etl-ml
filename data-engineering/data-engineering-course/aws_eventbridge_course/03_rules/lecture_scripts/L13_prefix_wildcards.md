---
lecture: L13
title: "Prefix Matching + Wildcards + Arrays"
duration: "11:00"
section: 3
prereqs: ["L12 (content filtering)"]
downloads:
  - "../../downloads/README.md"
---

# L13 — Prefix Matching, Wildcards, Arrays

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 3 — Rules + Event Patterns
> **Duration:** 11:00

## Prereqs

- L12 — content filtering on `source`, `detail-type`, `detail`, `time`.

## Key terms

- **Operator** — a special object form inside a pattern array. E.g.
  `{"exists": true}`, `{"prefix": "users/"}`, `{"numeric": [">=", 5]}`.
- **Exists** — checks whether a field is present on the event.
- **Numeric** — numeric comparison (`>`, `>=`, `<`, `<=`, `==`).
- **Prefix / suffix** — string prefix / suffix matching.
- **Anything-but** — negative match against a list of values.
- **CIDR** — IP-address range match.
- **Equals-ignore-case** — case-insensitive exact match.

## Lecture

Hi, I'm Prem Vishnoi. In L12 we filtered with the **literal form**
of patterns — strings, numbers, arrays. That gets you 80% of the
way. In this lecture we cover the **operator form** — the JSON
objects inside arrays that let you do `>`, `<`, `prefix`, `exists`,
and the rest. These are the operators that turn event patterns from
exact equality into a real matching language.

### The operator form

Inside a pattern array, you can put either literals (strings,
numbers) or **operator objects**. An operator object has a single
key that names the operator, and a value that is the operator's
argument:

```json
// Literal form — matches if event.source == "my.app"
{ "source": ["my.app"] }

// Operator form — matches if event.source starts with "my."
{ "source": [{ "prefix": "my." }] }

// Operator form — matches if event.detail exists
{ "detail": [{ "exists": true }] }
```

The operator object sits **inside the array**, just like a literal
would. You can mix literals and operators in the same array:

```json
// Match "my.app" OR any source that starts with "partner."
{ "source": ["my.app", { "prefix": "partner." }] }
```

### `exists` — guard against missing fields

`exists` is the most commonly missed operator. By default, a pattern
key fails when the event doesn't have the field. With `exists: true`
you invert the check: the pattern matches **only if** the field is
present, regardless of its value:

```json
// Match any event that has a "reason" field in detail
{ "detail": { "reason": [{ "exists": true }] } }
```

`exists: false` matches the opposite: the field is missing. Useful
for distinguishing "the order was placed without specifying a
channel" from "the order specified `channel: 'web'`".

### `numeric` — comparisons on numbers

The `numeric` operator takes an array of the form
`[operator, value]`:

```json
{ "detail": { "total": [{ "numeric": [">=", 1000] }] } }
{ "detail": { "items": [{ "numeric": ["<", 100] }] } }
{ "detail": { "qty": [{ "numeric": ["==", 1] }] } }
```

Operators: `>`, `>=`, `<`, `<=`, `==`. The event value is coerced
to a number; if the event value is a string that doesn't parse, the
pattern fails for that key.

Multiple `numeric` conditions OR together inside the same array:

```json
// total < 0 OR total > 1000
{ "detail": { "total": [{ "numeric": ["<", 0] }, { "numeric": [">", 1000] }] } }
```

### `prefix` and `suffix` — string boundaries

`prefix` matches if the event value starts with the argument;
`suffix` matches if it ends with the argument:

```json
{ "source": [{ "prefix": "aws." }] }     // any AWS service event
{ "detail": { "userId": [{ "prefix": "users/" }] } }   // tenant-style IDs
{ "detail": { "filename": [{ "suffix": ".csv" }] } }   // CSV uploads only
```

`prefix` is the workhorse of resource-based patterns. A common
pattern: match every event whose `resources` array contains an
object under your S3 bucket:

```json
{ "resources": [{ "prefix": "arn:aws:s3:::my-bucket/" }] }
```

### `anything-but` — negation

`anything-but` matches if the event value is **not** in the
argument list. There are four forms:

```json
{ "detail-type": [{ "anything-but": ["Order Cancelled"] }] }     // not a cancellation
{ "source": [{ "anything-but": { "prefix": "aws." } }] }          // not an AWS service event
{ "detail": { "channel": [{ "anything-but": ["phone"] }] } }      // not phone
{ "detail": { "ip": [{ "anything-but": { "cidr": "10.0.0.0/8" } }] } }  // not from internal network
```

Note: `anything-but` cannot be the sole filter for a top-level
required field if you also need the field to be present — combine
with `exists` if you want a "field is present AND not equal to X"
check.

### `cidr` — IP address ranges

The `cidr` operator matches an event's IP against a CIDR range:

```json
{ "detail": { "ip": [{ "cidr": "192.0.2.0/24" }] } }
{ "detail": { "ip": [{ "cidr": "2001:db8::/32" }] } }   // IPv6 works too
```

Useful for security patterns: only allow admin actions from your
office network, or only react to logins from outside a known IP
range.

### `equals-ignore-case` — case-insensitive exact match

For when the producer is sloppy with casing:

```json
{ "detail": { "country": [{ "equals-ignore-case": "us" }] } }
```

This matches `US`, `us`, `Us`, `uS`. Less common than `prefix`
but useful for region-style codes.

### Wildcards: what EventBridge does NOT have

EventBridge event patterns do **not** support glob wildcards
(`*`, `?`). They support `prefix`, `suffix`, `exists`,
`anything-but`, `numeric`, `cidr`, and `equals-ignore-case`. There
is no "any character in the middle" pattern — for that, use
multiple `prefix` patterns or a `suffix` combined with a `prefix`
clause. (The console used to show a `*` syntax that translated to
one of these operators; if you see `*` in older docs, mentally
replace it with `prefix`.)

### Array fields — element-wise match

When the event field is an **array** (e.g. `resources`), the
pattern matches if **any** element of the event array matches the
pattern value. So:

```json
// Event:  "resources": ["arn:aws:s3:::bucket-a/key1", "arn:aws:s3:::bucket-b/key2"]
// Pattern matches because "arn:aws:s3:::bucket-a/" is a prefix of the first element.
{ "resources": [{ "prefix": "arn:aws:s3:::bucket-a/" }] }
```

You don't have to use a loop or `$elemMatch` — EventBridge's
matching is element-wise on the event side, and array-on-pattern
side is OR over its literals/operators.

### A worked example: alert on critical S3 deletes

You want to fire an alert when **any object under a specific S3
prefix** is **deleted** by **someone other than your service
account**:

```json
{
  "source": ["aws.s3"],
  "detail-type": ["AWS API Call via CloudTrail"],
  "detail": {
    "eventName": ["DeleteObject"],
    "requestParameters": {
      "bucketName": ["critical-bucket"],
      "key": [{ "prefix": "production/" }]
    },
    "userIdentity": {
      "accountId": [{ "anything-but": ["123456789012"] }]
    }
  }
}
```

Five constraints, three of them using operator forms. This is the
shape of a real production pattern.

## Hands-on

No separate demo. The full set of operators is exercised in the
`test_put_rule.py` suite covered in L15.

## Quiz prep

- Where does the operator object go in the pattern? (Inside the
  value array.)
- What does `{"exists": true}` do? (Matches if the field is
  present.)
- What does `{"numeric": [">=", 5]}` mean? (Event value is `>= 5`.)
- Does EventBridge support `*` wildcards? (No — use `prefix` /
  `suffix` / `anything-but`.)

## Further reading

- AWS docs: [EventBridge event patterns — content filtering](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html#eb-filtering-operators)
- [`./L14_cross_account.md`](./L14_cross_account.md) — next lecture

## What's next

L14 — **Cross-Account + Cross-Region Event Patterns** — when the
event comes from a different account or a different region than
the rule, you need a resource policy on the bus. We cover the
trust policy, the `PutEvents` API, and the practical limits.
