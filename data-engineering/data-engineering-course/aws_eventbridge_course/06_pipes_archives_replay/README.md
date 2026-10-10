# Section 6 — Pipes + Archives + Replay (L25–L29)

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

This section covers the three features that turn EventBridge from
"pub/sub + cron" into a **complete** event-driven platform:

- **Pipes** — point-to-point integration between a stream/queue
  source and a single target, with optional filtering and
  enrichment.
- **Archives** — 30-day event backups, attached to a single bus.
- **Replay** — time-bounded re-delivery of archived events to a
  destination bus or Lambda.

By the end of the five lectures you will know when to use a Pipe
versus a Rule, how to opt in to partial batch response, how to
create an archive and what it costs, and how to start a replay
with a precise time range.

## Lecture map

| L# | Title | File |
|---|---|---|
| L25 | Pipes 101 (source → filter → enrich → target) | `lecture_scripts/L25_pipes_101.md` |
| L26 | Partial batch response (failure isolation) | `lecture_scripts/L26_partial_batch.md` |
| L27 | Archives (the event backup) | `lecture_scripts/L27_archives.md` |
| L28 | Replay (the killer feature) | `lecture_scripts/L28_replay.md` |
| L29 | Section recap + `archive_replay.py` walk-through | `lecture_scripts/L29_section_recap.md` |

## What the demo does

`code/archive_replay.py` is an **idempotent** boto3 program that
exercises the full archive-and-replay workflow end to end:

1. Creates a custom event bus `orders-bus` (idempotently).
2. Creates a dedicated replay bus `orders-replay-bus` (idempotently).
3. Creates a 30-day archive `orders-archive-30d` against the
   `orders-bus`.
4. Sends 5 synthetic `Order Placed` events to the bus.
5. Starts a `start_replay` for the last 1 hour, with the replay
   bus as the destination.

The script uses `boto3.client("events")` for bus, archive, and
replay operations, and supports `--dry-run` so you can review
the boto3 payload before any real AWS call. Idempotency is
provided by `ConflictException`-aware helpers
(`ensure_event_bus`, `ensure_archive`).

A note on moto support: as of `moto` 5.x, the unified `mock_aws`
decorator supports `create_event_bus`, `create_archive`,
`put_events`, `list_archives`, and `start_replay` (with the
caveat that both source and destination buses must exist in the
mock). The demo and tests use `mock_aws`, with comments
documenting the moto limitations in older pinned CI environments.

## What the tests do

`code/test_archive_replay.py` runs **6 tests**:

- 3 pure-Python unit tests on the time-range builder and the
  replay payload shape.
- 2 moto tests (`mock_aws`) that verify idempotent bus/archive
  creation and the dry-run path.
- 1 validation test that the API requires both source and
  destination buses to exist.

## How to run

```bash
# Dry-run — no AWS calls, just prints the boto3 payloads
python3 06_pipes_archives_replay/code/archive_replay.py --dry-run

# Real AWS — idempotent
python3 06_pipes_archives_replay/code/archive_replay.py

# Run the tests
python3 -m pytest 06_pipes_archives_replay/code/test_archive_replay.py -v
```

## Quiz

See `../quizzes/section_6.md` for 10 questions on Pipes vs
Rules, partial batch response, archives, and replay.
