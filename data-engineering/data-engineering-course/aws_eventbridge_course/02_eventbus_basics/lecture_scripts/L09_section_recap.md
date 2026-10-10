---
l_id: L09
title: "Section Recap + create_event_bus.py + tests"
duration: "8:00"
prereqs:
  - L08 (Partner Event Bus)
---

# L09 — Section Recap + create_event_bus.py walk-through

> **Section:** 2 — EventBus Basics
> **Duration:** 8:00

## Prereqs

- L08 — Partner Event Bus

## Key terms

- **Idempotent script** — a script you can run once or a hundred
  times and the end state is the same. For `create_event_bus.py`,
  re-running should not raise and should not create duplicate
  resources.
- **`ResourceAlreadyExistsException`** — the boto3 error raised by
  `CreateEventBus` when a bus with the same name already exists in
  the (account, region). The script catches this and treats it as
  a no-op.
- **Dry-run** — execute the script's logic *without* making any
  AWS calls. Implemented here as a `--dry-run` CLI flag and verified
  in tests with a `unittest.mock.patch` on `boto3.client`.

## Lecture

We close section 2 with a quick recap of the section's vocabulary,
then walk through `02_eventbus_basics/code/create_event_bus.py`
end-to-end. By the end of this lecture you should be able to read
the script, predict what it does on first run vs second run, and
explain how the tests prove it.

### Section 2 recap — the 5 lectures in one minute

- **L05 — What is an event bus?** A logical router inside
  EventBridge. Regional, account-scoped, addressed by ARN.
- **L06 — The default bus.** Auto-created, undeletable, name is
  `default`. Receives AWS service events, custom `PutEvents`, and
  scheduled events.
- **L07 — Custom bus.** A bus you create with `CreateEventBus`.
  Free. Used for isolation, environment separation, and
  cross-principal sharing.
- **L08 — Partner bus.** A bus for SaaS integrations. Name starts
  with `aws.partner/`. Auth is a resource policy on the bus.
- **L09 — This lecture.** We turn L05–L08 into a real, idempotent
  boto3 script with `moto` tests.

### The script in plain English

`create_event_bus.py` does four things, in this order:

1. **Create a custom bus** named `acme-orders` (override with
   `--name`). If the bus already exists in this
   (account, region), it catches `ResourceAlreadyExistsException`
   and continues — that's the idempotency.
2. **Apply a resource policy** to the bus. The policy grants a
   specific AWS account (override with `--source-account`) the
   `events:PutEvents` action on this bus. AWS requires a resource
   policy before cross-account publishing works, so the script
   attaches one even if you don't intend to use it — you can edit
   the policy later.
3. **List every bus** in the (account, region) and print its name
   and ARN. This is the verification step — you can eyeball that
   your new bus is present.
4. **Print a summary** with the bus ARN, the policy summary, and
   the next-step hint ("now attach a rule, see L10").

A `--dry-run` flag short-circuits at the top: nothing is created,
no policy is attached, no list call is made. The script just
prints what *would* happen. This is verified in the tests by
patching `boto3.client` and counting how many times each method
is called.

### Walk-through of the key functions

```python
def ensure_event_bus(client, name: str) -> str:
    """Create the bus if missing; return its ARN either way."""
    try:
        resp = client.create_event_bus(Name=name)
        LOG.info("created bus %s", name)
        return resp["EventBusArn"]
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ResourceAlreadyExistsException":
            arn = describe_event_bus_arn(client, name)
            LOG.info("bus %s already exists; reusing arn=%s", name, arn)
            return arn
        raise
```

The function is **idempotent by construction**: first call creates,
second call hits the exception, third call also hits the exception
— and in all three cases you get back the same ARN. That's the
property the test suite asserts.

```python
def apply_resource_policy(
    client, name: str, *, source_account: str, principal: str
) -> None:
    """Grant another account the right to PutEvents on this bus."""
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "AllowCrossAccountPutEvents",
            "Effect": "Allow",
            "Principal": {"AWS": f"arn:aws:iam::{source_account}:root"},
            "Action": "events:PutEvents",
            "Resource": describe_event_bus_arn(client, name),
        }],
    }
    client.put_permission(EventBusName=name, Policy=policy)
    LOG.info("applied resource policy to bus %s", name)
```

The policy is a plain dict, JSON-serializable. We send it via
`put_permission`, which is the correct API for a *resource policy*
on an event bus (as opposed to an IAM policy, which would attach to
an identity).

```python
def list_buses(client) -> list[dict]:
    """Return [{'Name': ..., 'Arn': ...}, ...] for every bus."""
    out: list[dict] = []
    paginator = client.get_paginator("list_event_buses")
    for page in paginator.paginate():
        for b in page["EventBuses"]:
            out.append({"Name": b["Name"], "Arn": b["Arn"]})
    return out
```

The list call is paginated — important because in a real account
you can have up to 100 buses. The script returns the list and
`main()` prints it.

### The dry-run path

The CLI flag is implemented at the top of `main()`:

```python
if args.dry_run:
    print(f"[dry-run] would create bus {args.name!r} in {args.region}")
    print(f"[dry-run] would attach policy allowing {args.source_account}")
    print(f"[dry-run] would list buses in {args.region}")
    return 0
```

In tests we patch `boto3.client` to a `MagicMock` and run
`main(["--dry-run", ...])`. We then assert that the patched client
was *never instantiated* (or, more precisely, that the methods we
expect to call — `create_event_bus`, `put_permission`,
`list_event_buses` — were never called). That's how we prove the
dry-run path makes zero AWS calls.

### The test suite

`test_create_event_bus.py` has **seven tests**, all under
`@mock_aws`:

| # | Test | What it proves |
|---|---|---|
| 1 | `test_creates_new_bus` | First call returns a new ARN and the bus is listed. |
| 2 | `test_recreate_is_idempotent` | Second call returns the same ARN and does not raise. |
| 3 | `test_apply_resource_policy` | `put_permission` was called with the right policy shape. |
| 4 | `test_list_buses_includes_ours` | After creation, our bus appears in the list. |
| 5 | `test_dry_run_makes_no_calls` | With `--dry-run`, no `boto3.client("events")` is instantiated. |
| 6 | `test_delete_bus` | `delete_event_bus` removes the bus; subsequent list excludes it. |
| 7 | `test_ensure_bus_helper_returns_arn` | The helper returns the same ARN on create and on reuse. |

You can run them from the course root with:

```bash
python3 -m pytest 02_eventbus_basics/code/test_create_event_bus.py -v
```

Expected: **7 passed** in under 2 seconds, no AWS calls.

### How to run the script for real

```bash
export AWS_REGION=us-east-1
python 02_eventbus_basics/code/create_event_bus.py \
    --name acme-orders \
    --source-account 444455556666
```

Re-run it as many times as you like — the output is the same.
Add `--dry-run` to see what it would do without spending a
`CreateEventBus` call.

## Hands-on

```bash
# From the course root
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-engineering-course/aws_eventbridge_course
python3 -m pytest 02_eventbus_basics/code/test_create_event_bus.py -v
```

All 7 tests should pass. Then look at `02_eventbus_basics/code/create_event_bus.py`
and trace each test back to the function it exercises.

## Quiz prep

- Why do we catch `ResourceAlreadyExistsException` in
  `ensure_event_bus`? (To make the script idempotent.)
- Which boto3 API attaches a resource policy to a bus? (`put_permission`.)
- How do we prove the `--dry-run` path makes no calls? (Patch
  `boto3.client` with a `MagicMock` and assert it was never
  instantiated.)

## Key takeaways

- Section 2's demo, `create_event_bus.py`, creates a **custom bus
  idempotently**, attaches a **resource policy**, and **lists
  buses**.
- Idempotency comes from catching `ResourceAlreadyExistsException`
  on `CreateEventBus`.
- The **dry-run path** returns early before any boto3 call; tests
  prove this by patching `boto3.client` with a `MagicMock`.
- The **test suite** is 7 tests under `@mock_aws`; no AWS account
  required.
- In section 3 we move on to **rules + event patterns** — the
  matching logic that decides *which* events on a bus get sent
  to which targets.

## Further reading

- _Amazon EventBridge API Reference_ — `CreateEventBus`,
  `PutPermission`, `ListEventBuses`
- `02_eventbus_basics/code/create_event_bus.py` — the script we
  walked through
- `02_eventbus_basics/code/test_create_event_bus.py` — the test
  suite
- L10 — Rules 101 (section 3)
