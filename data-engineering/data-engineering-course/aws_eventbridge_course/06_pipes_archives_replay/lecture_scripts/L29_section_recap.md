---
lecture: L29
title: "Section 6 Recap + Walk-Through of archive_replay.py"
duration: "8:30"
section: 6
prereqs:
  - L25
  - L26
  - L27
  - L28
downloads:
  - "../../downloads/eventbridge_cheat_sheet.pdf"
---

# L29 — Section 6 Recap + Walk-Through of `archive_replay.py`

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 6 — Pipes + Archives + Replay
> **Duration:** 8:30

## Prereqs

- Watched **L25, L26, L27, L28** in this section.
- Python 3.11+ and `requirements.txt` dependencies installed
  (`boto3`, `moto[events]`, `pytest`).

## Key terms

- **Idempotent script** — safe to re-run. The demo uses
  `create_event_bus` + `try/except ConflictException`,
  `create_archive` + `try/except ConflictException`, and
  `describe_replay` to check for an existing replay.
- **`--dry-run`** — a CLI flag that prints the boto3 call we
  *would* have made, without making it. Every script in this
  course supports it.
- **Archive + replay** — the two halves of EventBridge's
  time-machine feature.
- **Replay bus** — a dedicated bus used as the destination for
  replays, so the live bus is not polluted with replayed events.

## Lecture

Hi, I'm Prem Vishnoi. Welcome to the section-6 recap. In the last
four lectures we covered Pipes (L25), partial batch response
(L26), Archives (L27), and Replay (L28). Now we put it all
together with a real, idempotent, dry-run-able boto3 program.

### The full set of section-6 concepts

| Lecture | Concept | How it shows up in code |
|---|---|---|
| L25 | Pipe = source + filter + enrichment + target | we focus on archive/replay in the demo, but the script is the same shape |
| L25 | Pipes vs Rules | Rules for 1-to-many; Pipes for point-to-point |
| L26 | Partial batch response | Lambda's `reportBatchItemFailures` field |
| L27 | Archive = 30-day event backup | `create_archive` with 30-day retention |
| L27 | Source bus is a custom bus, not default | we create `orders-bus` |
| L28 | Replay = time-bounded re-delivery | `start_replay` with `EventStartTime` / `EventEndTime` |
| L28 | Replay is **not** idempotent | documented in the demo's docstring |

### Walk-through of `06_pipes_archives_replay/code/archive_replay.py`

Open the file. The script has four logical sections:

#### 1. Constants and the `REPLAY_WINDOW_HOURS` knob

```python
BUS_NAME = "orders-bus"
REPLAY_BUS_NAME = "orders-replay-bus"
ARCHIVE_NAME = "orders-archive-30d"
REPLAY_NAME = "orders-replay-last-hour"
REPLAY_WINDOW_HOURS = 1
```

These are intentionally editable — the script is meant to be
forked and re-purposed. `REPLAY_WINDOW_HOURS` is the most
commonly changed value: set to 1 for a smoke test, 24 for a
backfill, 720 for a 30-day replay.

#### 2. `ensure_event_bus(client, name, dry_run)`

Idempotent `create_event_bus` with a `try/except ConflictException`
fallback. The function is the same shape as
`ensure_schedule_group` from L24 — same pattern across the
course.

#### 3. `ensure_archive(client, bus_name, archive_name, dry_run)`

Calls `create_archive` with a 30-day retention. The
`EventSourceArn` is the bus ARN. We also handle the case where
the archive already exists (ConflictException → skip).

#### 4. `send_test_events(client, bus_name, count, dry_run)`

The demo's "make sure the archive has something in it" function.
It calls `put_events` with `count` synthetic events shaped like
real order events:

```python
events.put_events(
    Entries=[
        {
            "Source": "demo.app",
            "DetailType": "Order Placed",
            "Detail": json.dumps({"orderId": f"o-{i}", "total": 42}),
            "EventBusName": bus_name,
        }
        for i in range(count)
    ]
)
```

In `--dry-run` mode it just prints the payload.

#### 5. `start_replay_for_last_window(client, …)`

The heart of the demo. It:

1. Computes `EventStartTime` and `EventEndTime` from
   `REPLAY_WINDOW_HOURS`.
2. Calls `start_replay` with the archive, the time range, and
   the replay bus as the destination.
3. Returns the `ReplayArn`.

In `--dry-run` mode it prints the `start_replay` payload.

#### 6. `describe_replay_if_exists(client, replay_name)`

A helper that wraps `describe_replay` with a
`ResourceNotFoundException` catch. Used in the test suite to
check replay state without crashing.

#### 7. `main()`

The CLI entry point. Parses `--dry-run` and `--region`, then
calls the four steps in order:

1. `ensure_event_bus(client, BUS_NAME, dry_run)`
2. `ensure_event_bus(client, REPLAY_BUS_NAME, dry_run)`
3. `ensure_archive(client, BUS_NAME, ARCHIVE_NAME, dry_run)`
4. `send_test_events(client, BUS_NAME, count=5, dry_run)`
5. `start_replay_for_last_window(client, …)`

Each step prints a `[ok]` or `[dry-run]` prefix so the demo's
output is easy to read.

### What the tests do

`test_archive_replay.py` has **6 tests**:

1. `test_build_replay_time_range` — pure-Python check that the
   `EventStartTime` / `EventEndTime` builder produces a window
   that is *exactly* the configured number of hours wide.
2. `test_replay_payload_shape` — pure-Python check that the
   `start_replay` payload has the required fields
   (`ReplayName`, `EventSourceArn`, `EventStartTime`,
   `EventEndTime`, `Destination`).
3. `test_dry_run_does_not_call_aws` — uses moto's `mock_aws` to
   prove that `--dry-run` does not create a bus, archive, or
   replay.
4. `test_create_event_bus_is_idempotent` — runs
   `ensure_event_bus` twice under `mock_aws`; the second call
   should not raise.
5. `test_create_archive_against_custom_bus` — under `mock_aws`,
   create the bus first, then the archive; assert both ARNs
   come back.
6. `test_replay_requires_existing_buses` — pure-Python
   validation of the "both source and dest buses must exist"
   rule that the API enforces.

A note on moto support for `start_replay`: moto 5.x supports
`start_replay` and `describe_replay`, but the implementation
requires both the source bus and the destination bus to exist
in the mock. The demo's idempotent helpers handle both cases
correctly.

### How to run it

```bash
# 1. Dry-run (no AWS calls)
python3 06_pipes_archives_replay/code/archive_replay.py --dry-run

# 2. With real AWS credentials (idempotent)
python3 06_pipes_archives_replay/code/archive_replay.py

# 3. In a specific region
python3 06_pipes_archives_replay/code/archive_replay.py --region us-west-2
```

The first run creates the bus, the archive, and starts the
replay. The second run is a no-op create (ConflictException
handled) and re-uses the existing archive. The replay itself
is not idempotent — re-running with the same name errors
out, which is the API's expected behavior.

### Common failure modes the demo guards against

| Failure | How the demo handles it |
|---|---|
| Bus already exists | `ConflictException` → swallow |
| Archive already exists | `ConflictException` → swallow |
| Replay name already exists | the demo does *not* handle this; the API returns `ResourceAlreadyExistsException`. Use a unique `REPLAY_NAME`. |
| `EventStartTime` >= `EventEndTime` | the time-range builder enforces a positive delta |
| No events in the time window | `start_replay` succeeds but replays 0 events |
| Source bus / dest bus does not exist | `ensure_event_bus` is called for both, in order |

## Hands-on

Run the demo locally:

```bash
cd 06_pipes_archives_replay/code
python3 archive_replay.py --dry-run
```

You should see five `[dry-run]` blocks: one for the source bus,
one for the replay bus, one for the archive, one for the test
events, and one for the replay. Then run the test suite:

```bash
cd /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-engineering-course/aws_eventbridge_course
python3 -m pytest 06_pipes_archives_replay/code/test_archive_replay.py -v
```

All 6 tests should pass. The `mock_aws` decorator provides a
fake AWS environment; no real AWS calls are made.

## Quiz prep

These are the section-6 recap questions to focus on:

- What's the difference between a Pipe and a Rule?
- How long does an archive retain events?
- Is `start_replay` idempotent? Why or why not?
- What is the partial batch response and how does a Lambda
  enable it?

## Further reading

- AWS docs: [EventBridge Pipes](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes.html)
- AWS docs: [EventBridge Archives](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-archive.html)
- AWS docs: [EventBridge Replay](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-replay.html)
- `../code/archive_replay.py` — the demo
- `../code/test_archive_replay.py` — the tests
- `../../quizzes/section_6.md` — section quiz
- `../../downloads/eventbridge_cheat_sheet.pdf` — one-page reference

## What's next

In **section 7** we cover **patterns + real-world**: schema
registry, cross-account buses, EventBridge + Step Functions,
S3 events, DynamoDB Streams, the 2026 cost model, and the
final course wrap-up. That section has no code demos — it is
all conceptual best practice.

**Ready? Let's close out the course.**
