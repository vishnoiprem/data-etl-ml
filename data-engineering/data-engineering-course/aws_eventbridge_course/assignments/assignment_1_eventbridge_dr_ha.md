# Assignment 1 — Build a Cross-Region EventBridge DR Pipeline

> **Optional extension exercise.** Combines everything in sections 2–7.

## Goal

Stand up a **cross-region** event-driven pipeline that:
1. Detects a specific event pattern in `us-east-1`.
2. Forwards the event to a custom event bus in `us-west-2`.
3. Archives the event for 30 days.
4. Sends the event to both a Lambda handler and an SNS topic.

## Steps

1. Create two custom event buses (one per region).
2. Create a rule on the `us-east-1` bus with an event pattern that
   matches `source: "my.app"` and `detail-type: "Order Placed"`.
3. Add a cross-region bus target: the rule forwards matching events
   to the `us-west-2` bus ARN.
4. On the `us-west-2` bus, add a second rule that matches the same
   pattern and fans out to (a) a Lambda and (b) an SNS topic.
5. Enable an archive on the `us-west-1` bus with a 30-day retention.
6. Replay the last 24 hours of archived events and verify both
   targets fire.

## Deliverable

A PR that adds:
- `boto3_dr_pipeline.py` (idempotent, both regions, with `--dry-run`)
- `tests/test_dr_pipeline.py` (moto, ≥ 6 tests)
- A `NOTES.md` describing one failure mode you engineered around
  (e.g. "the archive is region-scoped, so a cross-region failover
  requires an S3 backup of the archive" — your choice).

## Bonus

- Add a **DLQ** on the Lambda target so failures land in SQS.
- Add a **schema** for the event in the Schema Registry.
- Add a **time-based filter** so the rule only fires during business
  hours in `America/Los_Angeles`.
