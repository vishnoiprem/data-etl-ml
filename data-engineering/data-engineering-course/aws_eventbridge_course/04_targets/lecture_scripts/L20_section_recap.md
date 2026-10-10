---
lecture: L20
title: "Section Recap + put_targets.py Walk-Through"
duration: "10:30"
section: 4
prereqs: ["L16-L19"]
downloads:
  - "../../downloads/README.md"
---

# L20 — Section 4 Recap + `put_targets.py` Walk-Through

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
> **Section:** 4 — Targets
> **Duration:** 10:30

## Prereqs

- L16–L19 (Targets 101 through DLQ + Retry Policies).
- L15 (Section 3 recap) — for the `put_rule.py` shape that
  `put_targets.py` extends.

## Key terms

- **IAM role for Lambda target** — assumed by EventBridge to call
  `lambda:InvokeFunction`. Required for Lambda/Step Functions;
  not needed for SQS/SNS (they use resource policies).
- **Target ID stability** — choosing target IDs that are derived
  from the target's role (function name, queue name) so the
  script is idempotent across re-runs.

## Lecture

Hi, I'm Prem Vishnoi. Welcome to the recap for Section 4. This is
the section that completes the EventBridge picture: we have
**events** (Section 2), **rules + patterns** (Section 3), and
now **targets + DLQ + retry** (Section 4). Once you have all
three, you can build any event-driven system.

### Section 4 — what you should remember

Six things, in order of importance:

1. **15+ target types**, but you'll use Lambda, SQS, SNS, and
   Step Functions 95% of the time.
2. **Lambda targets are async** by default. EventBridge invokes
   them and forgets; the result is a CloudWatch metric, not a
   return value.
3. **SQS and SNS targets don't need an execution role** — they
   use resource policies on the queue/topic.
4. **Lambda and Step Functions DO need an execution role** —
   EventBridge assumes it to call the target.
5. **Retry policy is per target**: `MaximumRetryAttempts` and
   `MaximumEventAgeInSeconds`.
6. **DLQ is mandatory for any critical target.** Without a DLQ,
   failed events are silently dropped.

### Walk-through: `code/put_targets.py`

The file follows the same shape as `put_rule.py`. Top-level
constants:

```python
BUS_NAME = "orders-bus"
RULE_NAME = "orders-placed-rule"
REGION = "us-east-1"

EVENT_PATTERN = {
    "source": ["my.app"],
    "detail-type": ["Order Placed"],
}

LAMBDA_TARGET_ID = "lambda-process-order"
SQS_TARGET_ID = "sqs-orders"
```

The pattern of "constants at the top, idempotent helpers in
the middle, CLI at the bottom" is the same one. Two new
helpers are added: `ensure_lambda_role` (creates an IAM role
for EventBridge to assume) and the `add_*_target` family.

The role helper:

```python
def ensure_lambda_role(iam, role_name: str) -> str:
    """Create an IAM role EventBridge can assume to invoke Lambda.

    moto's IAM mock understands assume-role-policy-document
    and policy ARNs. We pass minimal policies to keep the demo
    self-contained.
    """
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "events.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    try:
        iam.get_role(RoleName=role_name)
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            raise
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy),
        )
    return f"arn:aws:iam::000000000000:role/{role_name}"
```

The role is just an IAM role; the actual `lambda:InvokeFunction`
permission is attached in a real deployment. For the demo we
keep the role bare and rely on `moto`'s permissive authorization.

The target-add helpers:

```python
def add_lambda_target(events_client, bus, rule, function_arn, role_arn,
                      target_id=LAMBDA_TARGET_ID, dlq_arn=None) -> str:
    target = {
        "Id": target_id,
        "Arn": function_arn,
        "RoleArn": role_arn,
    }
    if dlq_arn:
        target["DeadLetterConfig"] = {"Arn": dlq_arn}
    resp = events_client.put_targets(
        Rule=rule, EventBusName=bus, Targets=[target]
    )
    if resp.get("FailedEntries"):
        raise RuntimeError(f"failed to add lambda target: {resp}")
    return target_id


def add_sqs_target(events_client, bus, rule, queue_arn,
                   target_id=SQS_TARGET_ID) -> str:
    resp = events_client.put_targets(
        Rule=rule, EventBusName=bus,
        Targets=[{"Id": target_id, "Arn": queue_arn}]
    )
    if resp.get("FailedEntries"):
        raise RuntimeError(f"failed to add sqs target: {resp}")
    return target_id
```

Each helper takes the `target_id` as a parameter (defaulting to
the module-level constant) so you can re-add the same target
under a different ID — useful for tests, and for migrating
between target configurations.

The remove/re-add pair:

```python
def remove_target(events_client, bus, rule, target_id) -> None:
    events_client.remove_targets(
        Rule=rule, EventBusName=bus, Ids=[target_id]
    )


def list_target_ids(events_client, bus, rule) -> list[str]:
    resp = events_client.list_targets_by_rule(Rule=rule, EventBusName=bus)
    return [t["Id"] for t in resp["Targets"]]
```

`list_target_ids` is what the test suite uses to assert that
"after I added a target, the list contains it" and "after I
removed it, the list does not".

The main entry point:

```python
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--region", default=REGION)
    args = parser.parse_args(argv)

    if args.dry_run:
        print(f"[dry-run] would ensure bus:    {BUS_NAME}")
        print(f"[dry-run] would ensure rule:   {RULE_NAME}")
        print(f"[dry-run] would add lambda target: {LAMBDA_TARGET_ID}")
        print(f"[dry-run] would add sqs target:    {SQS_TARGET_ID}")
        return 0

    events = boto3.client("events", region_name=args.region)
    iam = boto3.client("iam", region_name=args.region)

    role_arn = ensure_lambda_role(iam, "EventBridgeInvokeLambda")
    # ... etc
    return 0
```

The dry-run branch is intentionally short — it prints what the
script *would* do, without making any AWS call. This is the
mode the test suite uses to verify the CLI is well-formed.

### Walk-through: `code/test_put_targets.py`

Six tests cover the full surface:

1. **test_add_single_target** — `add_lambda_target` returns the
   target ID; `list_target_ids` includes it.
2. **test_add_multiple_targets** — both Lambda and SQS targets
   are added; the list contains both IDs.
3. **test_target_ids_are_unique** — adding the same target
   twice (with the same ID) does not produce duplicates.
4. **test_remove_target** — after `remove_target`, the list does
   not contain the ID.
5. **test_idempotent_re_add** — re-running the full setup
   (bus + rule + 2 targets) leaves the system in the same
   state, with the same two target IDs.
6. **test_dry_run** — running the CLI with `--dry-run` does not
   create any resources; `list_targets_by_rule` 404s on the
   rule (or returns an empty list, depending on the moto
   version).

The fixture pattern is identical to `test_put_rule.py`:

```python
@pytest.fixture
def client():
    return put_targets._events_client(region=REGION)


@pytest.fixture
def bus_rule(client):
    put_targets.ensure_bus(client, put_targets.BUS_NAME)
    put_targets.ensure_rule(client, put_targets.BUS_NAME,
                            put_targets.RULE_NAME,
                            put_targets.EVENT_PATTERN)
    return client, put_targets.BUS_NAME, put_targets.RULE_NAME
```

`moto` state is per-test, so the `@mock_aws` decorator on each
test gives a clean slate.

### Running the demo

```bash
# From the course root
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-engineering-course/aws_eventbridge_course

# Dry-run (no AWS)
python3 04_targets/code/put_targets.py --dry-run

# Tests
python3 -m pytest 04_targets/code/test_put_targets.py -v
```

Expected: 6 tests pass in under 2 seconds.

## Hands-on

```bash
# 1. Dry-run
python3 04_targets/code/put_targets.py --dry-run

# 2. Tests
python3 -m pytest 04_targets/code/test_put_targets.py -v

# 3. Real AWS (only if you have a sandbox account)
python3 04_targets/code/put_targets.py
aws events list-targets-by-rule --rule orders-placed-rule \
    --event-bus-name orders-bus
```

After this, take [`../quizzes/section_4.md`](../quizzes/section_4.md)
to lock in the target types, the retry policy, and the DLQ.

## Quiz prep

- What's the difference between a Lambda target and an SQS
  target's authorization model? (Lambda: execution role.
  SQS: resource policy on the queue.)
- What's the max event age on a retry policy? (Configurable;
  default is 24 hours.)
- Why do we need a DLQ? (Failed events are otherwise dropped.)
- What's the operational signal that a DLQ has messages?
  (CloudWatch alarm on `ApproximateNumberOfMessagesVisible`.)

## Further reading

- [`code/put_targets.py`](../code/put_targets.py) — the demo script
- [`code/test_put_targets.py`](../code/test_put_targets.py) — the test suite
- [`../quizzes/section_4.md`](../quizzes/section_4.md) — Section 4 quiz
- [`../README.md`](../README.md) — Section 4 overview

## What's next

Section 5 — **EventBridge Scheduler (L21–L24)** — the time-based
trigger. Cron + rate expressions, one-off schedules, time zones.
Same `put_rule` API surface, different trigger.
