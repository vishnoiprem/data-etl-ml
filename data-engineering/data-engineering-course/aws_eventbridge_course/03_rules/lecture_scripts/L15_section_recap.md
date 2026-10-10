---
lecture: L15
title: "Section Recap + put_rule.py Walk-Through"
duration: "9:50"
section: 3
prereqs: ["L10-L14"]
downloads:
  - "../../downloads/README.md"
---

# L15 — Section 3 Recap + `put_rule.py` Walk-Through

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 3 — Rules + Event Patterns
> **Duration:** 9:50

## Prereqs

- L10–L14 (Rules 101 through Cross-Account).

## Key terms

- **Idempotent** — safe to re-run; the second run has the same end
  state as the first.
- **`describe_rule`** — the read API for a single rule. Returns
  `Name`, `Arn`, `EventPattern`, `State`, `EventBusName`, etc.
- **`@mock_aws`** — the `moto` decorator that mocks every AWS
  service for the duration of a test.

## Lecture

Hi, I'm Prem Vishnoi. Welcome to the recap lecture for Section 3.
We covered a lot of ground in five lectures: rules, exact-match
semantics, content filtering, operator forms, and cross-account
patterns. In this lecture we tie it all together by walking
through `put_rule.py` and its test suite, and then you'll run
the quiz.

### Section 3 — what you should remember

Six things, in order of importance:

1. **A rule is a filter + a route.** The event pattern decides
   what matches; the target list decides where matched events go.
2. **Event patterns are exact-match by default**, with operators
   (`prefix`, `numeric`, `exists`, `anything-but`, `cidr`,
   `equals-ignore-case`) layered on top.
3. **AND over keys, OR inside arrays.** That's the entire matching
   model.
4. **The four content fields** you'll filter on most:
   `source`, `detail-type`, `detail.<field>`, `time`.
5. **`ENABLED` vs `DISABLED`** — disabled rules still match but
   don't fire targets. Useful for staged rollouts.
6. **Cross-account** requires a resource policy (`put_permission`)
   on the destination bus.

### Walk-through: `code/put_rule.py`

Open the file:

```python
import argparse
import json
import sys

import boto3
from botocore.exceptions import ClientError

BUS_NAME = "orders-bus"
RULE_NAME = "orders-placed-rule"
EVENT_PATTERN = {
    "source": ["my.app"],
    "detail-type": ["Order Placed"],
}


def _events_client(region: str = "us-east-1") -> boto3.client:
    """Construct an EventBridge client. moto intercepts this when active."""
    return boto3.client("events", region_name=region)
```

The top of the file is constants and a thin wrapper. The
`EVENT_PATTERN` is a Python dict — `put_rule` requires it as a
JSON string, so we serialize with `json.dumps` at the call site
(not in the constant).

The interesting function is `ensure_rule`:

```python
def ensure_rule(client, bus_name: str, rule_name: str, pattern: dict,
                state: str = "ENABLED") -> str:
    """Create or update a rule idempotently. Returns the rule ARN."""
    try:
        resp = client.put_rule(
            Name=rule_name,
            EventBusName=bus_name,
            EventPattern=json.dumps(pattern),
            State=state,
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            raise RuntimeError(f"event bus {bus_name!r} not found") from e
        raise
    return resp["RuleArn"]
```

`put_rule` is **idempotent on its own** — if the rule exists, the
call updates it. If the bus doesn't exist, the call raises
`ResourceNotFoundException`, which we wrap as a friendlier error.
We don't catch and retry; we want the script to fail loudly if the
bus is missing, because that's a config bug.

The `ensure_bus` function follows the same pattern:

```python
def ensure_bus(client, bus_name: str) -> str:
    """Create a custom bus if it doesn't exist. Returns the bus ARN."""
    try:
        client.describe_event_bus(Name=bus_name)
        return f"arn:aws:events:us-east-1:000000000000:event-bus/{bus_name}"
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise
    client.create_event_bus(Name=bus_name)
    return f"arn:aws:events:us-east-1:000000000000:event-bus/{bus_name}"
```

`describe_event_bus` is the cheapest read; we use it as the
"does it exist?" probe. If it doesn't, we create. Note that we
hard-code the account ID `000000000000` — that's the AWS
account ID `moto` uses for mocked calls. In a real AWS script
you'd use `boto3.client("sts").get_caller_identity()["Account"]`.

The `describe` function:

```python
def describe(client, bus_name: str, rule_name: str) -> dict:
    return client.describe_rule(Name=rule_name, EventBusName=bus_name)
```

Returns the full rule descriptor including the parsed
`EventPattern` (as a string, since that's what the API returns).

And the main entry point:

```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would happen, but make no AWS calls.")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args(argv)

    client = _events_client(region=args.region)

    if args.dry_run:
        print(f"[dry-run] would ensure bus:    {BUS_NAME}")
        print(f"[dry-run] would ensure rule:   {RULE_NAME}")
        print(f"[dry-run] pattern:              {json.dumps(EVENT_PATTERN)}")
        print(f"[dry-run] state:                ENABLED")
        return 0

    ensure_bus(client, BUS_NAME)
    rule_arn = ensure_rule(client, BUS_NAME, RULE_NAME, EVENT_PATTERN)
    desc = describe(client, BUS_NAME, RULE_NAME)
    print(f"rule arn: {rule_arn}")
    print(f"state:    {desc['State']}")
    print(f"pattern:  {desc['EventPattern']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

The `--dry-run` flag short-circuits before any AWS call. This is
a 4-line pattern: parse args, build client, branch on dry-run, do
the work. The same shape works for `put_targets.py` in Section 4.

### Walk-through: `code/test_put_rule.py`

The test file uses the standard `moto` pattern: a
`@mock_aws` decorator on every test, no shared fixtures (moto's
state is per-decorator, and we want each test isolated).

```python
import json
import pytest
from botocore.exceptions import ClientError

from put_rule import (
    BUS_NAME, EVENT_PATTERN, RULE_NAME,
    ensure_bus, ensure_rule, describe, _events_client,
)


@pytest.fixture
def client():
    return _events_client(region="us-east-1")
```

Six tests cover the full surface:

1. **test_ensure_bus_creates_then_idempotent** — first call creates,
   second call does not raise.
2. **test_ensure_rule_returns_arn** — the rule exists, has the
   right pattern, and is `ENABLED`.
3. **test_pattern_matches** — sends a matching `PutEvents` and
   asserts the event is accepted (no exception).
4. **test_pattern_does_not_match_different_source** — sends an
   event with a different `source`; the call succeeds (PutEvents
   always returns success for well-formed events), but the rule
   doesn't fire. We test the rule's behavior via
   `test_event_matches_pattern` (a helper that runs the same
   matching logic the API would).
5. **test_disable_rule** — calls `disable_rule`, asserts the
   `State` is `DISABLED`.
6. **test_dry_run** — runs `main(["--dry-run"])`, asserts the
   exit code is 0 and no rule was created.

The matching helper is a small piece of code that mirrors what
EventBridge does on the server. (We don't have access to the real
matcher in `moto`; the test uses a local re-implementation for
exact-match verification only.)

### Running the demo

```bash
# From the course root
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-engineering-course/aws_eventbridge_course

# Dry-run (no AWS)
python3 03_rules/code/put_rule.py --dry-run

# Run the tests (offline, with moto)
python3 -m pytest 03_rules/code/test_put_rule.py -v
```

Expected: 6 tests pass in under 2 seconds.

## Hands-on

```bash
# 1. Dry-run
python3 03_rules/code/put_rule.py --dry-run

# 2. Tests
python3 -m pytest 03_rules/code/test_put_rule.py -v

# 3. Real AWS (only if you have a sandbox account)
python3 03_rules/code/put_rule.py
aws events list-rules --event-bus-name orders-bus
```

After this, take [`../quizzes/section_3.md`](../quizzes/section_3.md)
to lock in the matching model and the operator forms.

## Quiz prep

- What does `--dry-run` do? (Prints intent without making calls.)
- How does the script handle a missing bus? (Fails loudly with
  a wrapped error.)
- Why is `describe_event_bus` the idempotency probe? (It's the
  cheapest read, and it returns the same shape whether the bus
  exists or 404s.)

## Further reading

- [`code/put_rule.py`](../code/put_rule.py) — the demo script
- [`code/test_put_rule.py`](../code/test_put_rule.py) — the test suite
- [`../quizzes/section_3.md`](../quizzes/section_3.md) — Section 3 quiz
- [`../README.md`](../README.md) — Section 3 overview

## What's next

Section 4 — **Targets (L16–L20)** — once a rule matches, where
does the event go? Lambda, SQS, SNS, Step Functions, dead-letter
queues, and the retry policy that makes a resilient system.
