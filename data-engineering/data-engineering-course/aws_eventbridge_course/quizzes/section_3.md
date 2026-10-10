# Section 3 Quiz — Rules + Event Patterns

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the
> question. At least 3 questions focus on event-pattern JSON syntax.

---

**Q1.** What are the two responsibilities of an EventBridge rule?

- A. Encrypt the event payload and log it to CloudWatch
- B. Filter events with an event pattern, route matched events to targets
- C. Create a custom event bus and define a default rule
- D. Generate a schedule and invoke a Lambda on a cron

<details><summary>Show answer</summary>

**B — Filter + route.** A rule pairs an event pattern (the filter) with one or more targets (the route). `put_rule` decides what matches; `put_targets` decides where it goes.

</details>

---

**Q2.** In a rule's `State` field, what's the difference between `ENABLED` and `DISABLED`?

- A. `ENABLED` runs in the primary region; `DISABLED` runs in a secondary region
- B. `ENABLED` is billable; `DISABLED` is free
- C. `DISABLED` rules still match events but do not invoke targets; `ENABLED` rules match and invoke
- D. `DISABLED` deletes the rule after 30 days

<details><summary>Show answer</summary>

**C.** A disabled rule still evaluates the event pattern (useful for metrics) but does not invoke any target. Toggle with `enable_rule` / `disable_rule`.

</details>

---

**Q3.** Event-pattern JSON: which pattern correctly matches events with `source` of `my.app` or `my.legacy`?

- A. `{ "source": "my.app" }`
- B. `{ "source": ["my.app", "my.legacy"] }`
- C. `{ "source": { "any": ["my.app", "my.legacy"] } }`
- D. `{ "source": [{ "prefix": "my." }] }`

<details><summary>Show answer</summary>

**B — `{ "source": ["my.app", "my.legacy"] }`.** Arrays inside a pattern value mean OR. The event's `source` must equal one of the array elements. Option A is wrong because the recommended form is an array (not a scalar). Option D would also match `my.other` (because of the prefix) but is broader than asked.

</details>

---

**Q4.** Event-pattern JSON: what does the following pattern match?

```json
{
  "detail": {
    "total": [{ "numeric": [">=", 1000] }],
    "currency": ["USD"]
  }
}
```

- A. Events where `total` is `1000` exactly and `currency` is anything
- B. Events where `total` is at least `1000` AND `currency` is `USD`
- C. Events where `total` is at most `1000` OR `currency` is `USD`
- D. Events where `total` is missing but `currency` is `USD`

<details><summary>Show answer</summary>

**B — `total >= 1000` AND `currency == "USD"`.** Keys at the same level are AND; the `numeric` operator inside the value array expresses the `>=` comparison. The event must satisfy both constraints.

</details>

---

**Q5.** Event-pattern JSON: what does `{ "detail": { "reason": [{ "exists": true }] } }` match?

- A. Events where `detail.reason` is the literal string `true`
- B. Events where `detail.reason` is present (regardless of value)
- C. Events where `detail.reason` is missing
- D. Events where `detail.reason` is a boolean

<details><summary>Show answer</summary>

**B — The field is present, regardless of value.** `{ "exists": true }` is the operator that matches on presence only. Use `{ "exists": false }` for the opposite (field is missing).

</details>

---

**Q6.** What does it mean when an event pattern is missing a key that's on the event?

- A. The pattern is invalid — every event field must be in the pattern
- B. The event automatically fails because there's an unmatched field
- C. The pattern ignores the field — the pattern only constrains the keys it lists
- D. EventBridge uses a default value

<details><summary>Show answer</summary>

**C — The pattern only constrains the keys it lists.** Extra event fields are ignored. The pattern is a subset of the event. This is why `{ "source": ["my.app"] }` matches an event with `source`, `detail-type`, `time`, and a `detail` payload — only `source` is constrained.

</details>

---

**Q7.** Is matching case-sensitive?

- A. Yes — by default `Order Placed` does not match `order placed`
- B. No — EventBridge normalizes all strings to lowercase
- C. Only for `detail-type`; other fields are case-insensitive
- D. Only inside `detail`; envelope fields are case-insensitive

<details><summary>Show answer</summary>

**A — Yes, case-sensitive.** Use the `equals-ignore-case` operator if you need case-insensitive matching: `[{ "equals-ignore-case": "us" }]`.

</details>

---

**Q8.** What does `anything-but` do in an event pattern?

- A. Matches any value, including missing fields
- B. Matches when the event value is **not** in the supplied list
- C. Truncates the pattern to the first matching key
- D. Acts as a wildcard inside the array

<details><summary>Show answer</summary>

**B — `anything-but` matches when the event value is not in the supplied list.** Example: `{ "detail-type": [{ "anything-but": ["Order Cancelled"] }] }` matches every `detail-type` except cancellations. It can also accept a nested operator like `{ "anything-but": { "prefix": "aws." } }`.

</details>

---

**Q9.** To forward events from a custom bus in `us-east-1` to a custom bus in `us-west-2` (same account), what must you do?

- A. Both buses must have the same name
- B. The destination bus must have a resource policy allowing `events:PutEvents` from the source account/region
- C. The source bus must be in `us-west-2` (the source region must match the destination)
- D. Cross-region forwarding is not supported; you must use a Lambda in between

<details><summary>Show answer</summary>

**B — Resource policy on the destination.** Use `put_permission` to add the policy: `events.put_permission(EventBusName="...", Action="events:PutEvents", Principal="<account>")`. The forwarding rule then targets the destination bus's full ARN. Option D is wrong — cross-region forwarding is supported.

</details>

---

**Q10.** A rule's `EventPattern` is updated by calling `put_rule` again with the same `Name`. What happens?

- A. The call fails because the rule already exists
- B. The rule is deleted and recreated (losing its targets)
- C. The pattern is replaced in place; targets are preserved
- D. A new rule is created with a generated suffix

<details><summary>Show answer</summary>

**C — The pattern is replaced in place; targets are preserved.** `put_rule` is naturally idempotent. The same is true for `put_targets` — re-calling with the same `Id` replaces the target. That's why both APIs are the right tool for "edit in place" scripts.

</details>
