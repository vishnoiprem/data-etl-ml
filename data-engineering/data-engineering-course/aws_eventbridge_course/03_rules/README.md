# Section 3 — Rules + Event Patterns (L10–L15)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Working artifact:** `code/put_rule.py` + `code/test_put_rule.py` (6 moto tests)
> **Quiz:** [`../quizzes/section_3.md`](../quizzes/section_3.md)

This section is where EventBridge gets its power. Section 2 taught you
about **event buses** (the highway). This section teaches you about the
**rules** that route traffic to specific **targets** based on the
**event pattern** JSON you attach to each rule.

If you only ever use one pattern, it will be **event-pattern
matching** — that's the entire focus of this section.

## Lecture map

| L# | Title | What you'll learn |
|---|---|---|
| **L10** | Rules 101 | What a rule is, the event-pattern-to-target mapping, ENABLED/DISABLED state |
| **L11** | Event Pattern Matching | The JSON predicate, exact-match semantics, how matching is evaluated |
| **L12** | Content Filtering | Filtering on `$.detail`, `$.detail-type`, `$.source`, `$.time` |
| **L13** | Prefix + Wildcards + Arrays | `"prefix": "users/"`, `"exists": true`, `"numeric": [">=", 5]` |
| **L14** | Cross-Account + Cross-Region | Event patterns across accounts and regions; resource policies |
| **L15** | Section Recap + `put_rule.py` | Walk through the demo, run the tests, take the quiz |

## What the demo does

`code/put_rule.py` is an **idempotent** boto3 script — safe to re-run
any number of times — that:

1. Creates a custom event bus named `orders-bus` (idempotent via
   `create_event_bus` / `describe_event_bus`).
2. Creates a rule named `orders-placed-rule` with an event pattern
   matching:
   ```json
   {
     "source": ["my.app"],
     "detail-type": ["Order Placed"]
   }
   ```
3. Ensures the rule is in `ENABLED` state.
4. Calls `describe_rule` and prints the response.

You can run it against real AWS (uses `~/.aws/credentials`) or against
`moto` for offline development.

```bash
# Dry-run (no AWS calls)
python3 03_rules/code/put_rule.py --dry-run

# Real AWS
python3 03_rules/code/put_rule.py

# Tests
python3 -m pytest 03_rules/code/test_put_rule.py -v
```

## Section quiz

After the lectures, take
[`../quizzes/section_3.md`](../quizzes/section_3.md) (10 questions,
including 3 dedicated to event-pattern JSON syntax).

## What's next

Section 4 — **Targets (L16–L20)** — adds the destination side of the
rule: Lambda, SQS, SNS, Step Functions, dead-letter queues, retry
policy.
