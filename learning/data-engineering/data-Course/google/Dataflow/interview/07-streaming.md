# Module 7 — Streaming

> **16 questions · Module 7 · Streaming**

---

## Event time and windows

### 1. Event time versus processing time — when must you use event time, and what breaks if you do not?

Use event time whenever the *time of the event* determines the answer — hourly revenue, sessionisation, SLA reporting, anything joined to a dimension that changes over time. Processing time is only correct when the question is literally "what arrived when", like a rate limit or a live operational counter.

The failure mode of using processing time is not a crash — it is a number that is quietly wrong. Events arrive out of order: a click from 14:59:58 that reaches the pipeline at 15:00:07. Under processing-time windowing it lands in the 15:00 bucket; under event-time windowing it lands in the 14:00 bucket where it belongs. At 3% late arrivals, every hourly total is off by a few percent, and the error is invisible because the totals still sum to the grand total.

The second, subtler failure: under processing time, a downstream consumer that reads "the 14:00 revenue" at 15:05 gets a number that will keep changing as more 14:00 events arrive. Under event time, once the window closes, the number is final. That property — finality — is what makes a result publishable.

In Beam, event time is carried by the element's timestamp, and you must set it explicitly; Beam defaults every element to the arrival timestamp. The course's `event_timestamp` helper returns `Timestamp(float(parse_timestamp(...).timestamp()))` — that is the whole mechanism.

### 2. What is the watermark, in one sentence?

The watermark is Beam's estimate of how far behind the input's event time can still be — it is the point in event time beyond which no new elements are expected, and it is what allows Beam to decide a window is finished and fire its trigger.

Two important clarifications. First, the watermark is **not** a clock; it advances based on observed event timestamps, typically with a configured hold-back or from an idle-source heuristic. Second, it is **monotonic** — it never goes backwards.

Beam's `WatermarkStrategy` is what computes it. In practice, a pipeline that reads from Pub/Sub gets a watermark that tracks the observed message timestamps, and a pipeline with an idle source needs `--idle_timeout` or an explicit hold-back so the watermark can advance past a gap.

### 3. Why is `AfterWatermark` combined with non-zero allowed lateness an error, and what does Beam actually do?

Because with allowed lateness greater than zero, the window can receive *more* data after the watermark has passed its end, which means a trigger that fires on the watermark has already emitted a result that is no longer final. Beam treats that as potentially losing data and refuses the combination unless you pass `--allow_unsafe_triggers`.

The concrete error is:

```text
ValueError: Unsafe trigger: AfterWatermark may lose data. Reason: MAY_FINISH
```

The subtlety that matters in practice: `AfterWatermark` is only *safe* when allowed lateness is exactly zero. `AfterCount` is never safe, because a window can close while elements are still in flight. So the "safe" configuration is `AfterWatermark()` with `allowed_lateness=0`, and the course's streaming pipeline defaults to exactly that — when `allowed_lateness_seconds` is non-zero and unsafe triggers are not enabled, it logs a warning and falls back to zero lateness so the run still succeeds.

### 4. `ACCUMULATING` versus `DISCARDING` — what is the difference, in numbers?

`ACCUMULATING` emits the window's **running total** every time the trigger fires. `DISCARDING` emits only the **delta** since the last firing, and the accumulated state is thrown away.

The numbers, from the course's own test: five events in one window with `AfterCount(2)`.

- `ACCUMULATING` emits counts of **2, 4, 5** — the running total at each firing.
- `DISCARDING` emits counts of **2, 2, 1** — the deltas. 2+2+1 = 5.

The choice is a contract with the downstream consumer. A consumer that *replaces* state (a BigQuery table partitioned by window, a `MERGE` on a key) wants `ACCUMULATING`. A consumer that *sums* what it receives (a streaming sink that appends, a per-minute counter) wants `DISCARDING`. Getting this wrong doubles or triples your numbers: an `ACCUMULATING` stream summed by the consumer counts the first two events twice and all five three times.

The practical default is `DISCARDING` for anything feeding an append-style sink, `ACCUMULATING` for anything feeding a replace-style sink or a checkpoint. And be explicit: Beam raises `ValueError: accumulation_mode must be provided for non-trivial triggers` if you use `AfterCount` or `AfterWatermark` without saying which.

### 5. Fixed versus sliding versus session windows — how do you choose?

**Fixed** (`FixedWindows(n)`) partitions time into non-overlapping intervals of length `n`. One event belongs to exactly one window. Use it for hourly/daily rollups, billing periods, anything where "the 14:00–15:00 bucket" is the natural unit. The cost is exactly one copy of each element.

**Sliding** (`SlidingWindows(size, period)`) produces overlapping windows. A 1-hour window every 15 minutes gives 4 windows per hour, and each element lands in 4 of them — 4× the aggregation work and 4× the output. Use it for rolling averages and rolling counts, where the answer genuinely needs the overlap.

**Session** (`SessionWindows(gap)`) closes a window when it sees a gap longer than `gap`. Use it for user sessions. The problem is that sessions are unbounded in duration: a user active for six hours produces one window containing six hours of events, and a `CombinePerKey` over that window keeps the accumulator alive for the whole session.

The rule: fixed unless the question is a rolling window or a session. The cost model is what convinces people — sliding windows are not free, they multiply both the shuffle and the state by `size / period`.

### 6. How does `allowed_lateness` change the numbers, and what does it cost?

With allowed lateness of `L` seconds, an event whose timestamp falls up to `L` seconds *after* a window's end can still be added to that window and will trigger a re-firing. The window's final value is only final after watermark + `L`.

The numbers: with a 1-hour window, a 5-minute lateness budget means a window can be updated until 5 minutes past the hour. A dashboard that publishes "the 14:00 total" must wait until 14:05 to be correct, and must handle the value *changing* if it published early.

The cost is state. Late data has to be held — the window's accumulator cannot be discarded until watermark + lateness has passed. With a 1-hour window and 5 minutes of lateness, you hold roughly 1/12 of an hour's worth of accumulators beyond what you would otherwise. Across a large key space that is real memory on the streaming workers, and it is the main reason `allowed_lateness` is not just "turn it on".

The failure story: a team set 24 hours of allowed lateness on a 5-minute window to catch a mobile client that buffered offline. State grew to hundreds of GB, workers began to be evicted by the streaming runner's memory limit, and the job thrashed. The fix was to reduce lateness to 10 minutes and handle the truly-old data with a separate late-arrival path.

### 7. What is the watermark-advance problem with multiple sources, and how do you solve it?

With two input sources, each has its own watermark, and Beam takes the **minimum** across the sources feeding a `WindowInto`. If one source is idle or slow, its watermark stalls and the merged watermark stalls with it — so no window ever fires, even though the busy source's data is long past.

This is the classic "one slow input poisons the whole pipeline" problem. The symptom is a dashboard that shows nothing after the first few minutes, with no errors anywhere.

The solutions, in order of preference:

1. **Bound the idle gap.** Set `--idle_timeout` so a source that produces nothing for N seconds is considered idle and its watermark is advanced to the current processing time. In Beam this is exposed on the source transform.
2. **Use a hold-back.** Configure the watermark to lag the observed max timestamp by a fixed amount, so it advances even when data stops.
3. **Reshape the data.** Move the merge *after* the aggregation where possible — aggregate each source independently and combine downstream, so a stalled source only delays its own results.

The production story: a pipeline merged a fast clickstream topic with a slow order-events topic that only produced a batch every hour. The merged watermark never advanced past the first hour, so the clickstream windows never fired. Fix: apply a hold-back on the watermark, and aggregate each source independently before merging.

---

## State, Pub/Sub and failure modes

### 8. What delivery guarantee does Pub/Sub give you, and what does Beam do about it?

Pub/Sub is **at-least-once** delivery. A message can be delivered more than once, and a message that was acknowledged can be redelivered if the ack was lost. Beam's `ReadFromPubSub` does not deduplicate; it will process a redelivered message again.

The mechanisms behind it: Pub/Sub retains an unacknowledged message and redelivers it if the subscriber's ack does not arrive within the ack deadline (default 10 seconds, maximum 600). Beam acks a message after the bundle containing it has been committed and checkpointed — so a worker that dies after processing but before the checkpoint commit causes a redelivery of the whole bundle.

So duplicates are not an error condition to be alerted on; they are a **fact of the design** that your pipeline must tolerate. The two standard defences:

- **Idempotent sink.** Write to a key that a re-write overwrites (`WriteToBigQuery` with `WRITE_TRUNCATE` on a partition, or a `MERGE` on a natural key). Then a duplicate is harmless.
- **Dedup by event id.** Keep a bounded set or a stateful `DoFn` of recently-seen `event_id`s and drop repeats. This is what the course's events carry an `event_id` field for.

### 9. How does `id_label` deduplication work, and what are its limits?

`id_label` is the Pub/Sub message attribute that carries a stable identifier for the message, and it is what Beam's Pub/Sub source uses to decide whether a message is new or a redelivery of one it has already delivered in this run.

The limits are sharp and worth stating in an interview. `id_label` deduplication is **per pipeline run**, not global and not durable: a new job starts with an empty seen-set. It also only works when the publisher actually sets the attribute — if your publisher does not set it, there is no deduplication at all, and the message is treated as new every time. And it deduplicates *the same message redelivered*, not *two genuinely distinct messages that happen to carry the same id*; if the publisher reuses an id for different payloads, `id_label` will drop the second one and you will lose data.

The production trap: a producer started setting `id_label` to a *business* key like the order id, then began republishing genuinely different updates for the same order. Beam saw the same `id_label`, treated the update as a redelivery, and dropped it. The pipeline "lost" legitimate updates with no error anywhere. The fix: the publisher must make `id_label` unique per *message*, and use a separate business key in the payload.

### 10. Two streaming jobs share one Pub/Sub subscription — what happens, and why is it a surprise?

**Messages are load-balanced between the jobs, not broadcast to both.** Each message goes to exactly one of the two subscribers, in round-robin fashion.

This surprises people because they assume Pub/Sub topics broadcast, like Kafka consumers... no, Kafka also load-balances within a consumer group. The surprise is the opposite one: a team running a "replay" job alongside the live job from the same subscription, expecting the replay to see all messages, discovered that the live job was silently receiving only half the traffic for the two months the replay job was running. Every aggregate in the live pipeline was wrong by roughly half, and it looked like a data-volume drop rather than a config mistake.

The rule: **one subscription, one job**. To have two independent readers, create two subscriptions on the same topic, each with its own backlog and its own retention. To have a replay, create a new subscription with `--ack-deadline` set generously and let it build up a backlog, then start a job on it — that is how you replay a historical window without disturbing production.

### 11. Why is a plain attribute not durable state, and what is the alternative?

A plain attribute on a `DoFn` — a field set on `self` — is **not durable state**. It lives in the Python object's memory in one worker process. When the worker is preempted, rescheduled or restarted, the attribute is gone. Beam checkpoints the *outputs* of a `DoFn` and the state of stateful transforms, but it does not checkpoint arbitrary instance attributes of a plain `DoFn`.

The alternative is the **stateful `DoFn` API**: `beam.transforms.userstate` with `ReadModifyWriteStateSpec` / `BagStateSpec`, accessed through `beam.transforms.userstate.on_timer` and the `Timer` param. Beam checkpoints that state with the bundle, so it survives a worker restart.

The production story is the classic one: a deduplicating `DoFn` that kept a `set` of seen event ids on `self`. It worked perfectly for two weeks. A worker was preempted by the platform during a spot-price spike, the set was lost, and the next 500,000 redelivered messages were all processed as new — double-counting a day's revenue in a single metric. Moving the seen-set into a `BagStateSpec` with a bounded size fixed it properly.

### 12. What does the stateful `DoFn` API look like, and what do you give up for it?

The shape is: subclass `beam.DoFn`, declare state specs as class attributes, get a `StateBag` and a timer in `process`, and use `@on_timer` to run code when the timer fires.

```python
from apache_beam.transforms.userstate import BagStateSpec, ReadModifyWriteStateSpec
from apache_beam.transforms.userstate import on_timer


class DedupeFn(beam.DoFn):
    SEEN = BagStateSpec('seen', beam.coders.VarIntCoder())
    COUNT = ReadModifyWriteStateSpec('count', beam.coders.VarIntCoder())

    def process(self, element, seen=beam.DoFn.StateParam(SEEN),
                count=beam.DoFn.StateParam(COUNT),
                timer=beam.DoFn.TimerParam(timer_id='flush')):
        key = element['event_id']
        if key in seen.read():
            return
        seen.add(key)
        count.write(count.read() + 1)
        timer.set('2026-01-15T10:05:00Z')

    @on_timer(timer_id='flush')
    def flush(self, count=beam.DoFn.StateParam(COUNT)):
        yield {'count': count.read()}
```

The trade-offs are real. State is **checkpointed**, which costs I/O on every bundle commit. State must be **keyed** — a `DoFn` with state requires the input to be a `KV`, which means a `GroupByKey`-style keyed stage, and that is a shuffle you may not have wanted. And the API is more complex than a `Map`.

You also give up the ability to reason about the state as a simple function of the input. The state is a function of the input *and* the checkpoint history, so a replay from a different checkpoint boundary can produce different intermediate values — though the final output must still be correct.

### 13. What are timers for, and how do processing-time timers differ from event-time timers?

A **timer** lets a stateful `DoFn` wake up later and do work: flush a buffer, emit a partial result, expire a key. Beam gives you two kinds.

**Processing-time timers** fire relative to wall-clock time as the runner sees it: `timer.set(duration=60)` fires 60 seconds of processing time later, whenever that is. They are **not** deterministic — the same input produces different outputs on different runs, because the firing time depends on real elapsed time. That makes them unusable in unit tests with `assert_that` on exact values, and unsuitable for anything that must be reproducible.

**Event-time timers** fire based on the *data's* time: `timer.set('2026-01-15T10:05:00Z')` fires when the watermark passes that instant. They are deterministic, and they are what you use for anything tied to the business clock — end-of-window flushes, session expiry, TTLs in event time.

The rule: use event-time timers for anything whose correctness depends on the data's timeline; use processing-time timers only for operational concerns (heartbeats, cache expiry) where reproducibility does not matter.

The production trap: a pipeline used a processing-time timer to emit "partial results every minute", and the automated test compared output row counts against a golden file. The test passed on a fast machine and failed on a loaded CI runner, because the timer fired a different number of times. Nobody could reproduce the failure locally. The fix was to drive the flushes from the data's timestamps instead.

### 14. How do you backfill historical data in a streaming pipeline?

You do not republish it into the live topic unless you have to — that pollutes the live pipeline and pollutes the subscription backlog. The three real options:

1. **A separate batch job over the same source of truth.** If the events are also written to GCS, BigQuery or a warehouse, backfill with a batch pipeline over the historical files. This is the right answer most of the time, and the same aggregation code can be shared between the batch and streaming paths — which is exactly why the course keeps the aggregation logic in `transforms.py` rather than inline in the pipeline.

2. **A replay subscription.** Create a new Pub/Sub subscription with the `retain_acked_messages` and `--ack-deadline` settings, let it accumulate the backlog, then run a job against it with the historical events' original timestamps. The pipeline's windowing will then produce the same windows as if the data had arrived live.

3. **File-based replay with `TestStream` or a bounded file source**, for a bounded historical range — but a streaming job reading a bounded file is a batch job wearing a streaming hat, and it does not restore the streaming semantics.

The trap in option 2 is that the replayed messages arrive with *their original publish timestamps* only if the publisher set them, and the watermark will move at the speed of the replay — so the job will hold a lot of state. Budget for it, and set the replay job's worker count up.

### 15. How do you test streaming logic deterministically, and what does `TestStream` give you?

`TestStream` lets you construct a timestamped stream element by element and advance the watermark explicitly, so the whole pipeline's behaviour — including late data and re-triggering — is reproducible in a unit test.

```python
from apache_beam.testing.test_stream import TestStream

events = (
    p
    | TestStream().add_elements(
        [TimestampedValue(b'{"region": "EMEA", "value": 10.0}', Timestamp(1000))],
        event_timestamp=Timestamp(1000),
    ).advance_watermark_to_infinity()
)
```

`advance_watermark_to_infinity()` is the important call: without it the watermark never passes any window's end, the trigger never fires, and the pipeline produces nothing — a test that "passes" while asserting nothing.

The determinism comes from the fact that the watermark only moves when you say so. That is what makes the late-data path testable: you emit an event whose timestamp falls in a window that has already fired, and you assert the window re-fires with the updated value. A real Pub/Sub source cannot give you that.

The practical advice: put the windowing logic behind a function that takes a `PCollection`, so the same code can be driven by `TestStream` in tests and by `ReadFromPubSub` in production. That is the pattern in `project/streaming_pipeline.py`, where `build_streaming_pipeline` takes an `events` PCollection as a parameter.

### 16. What is the memory cost of lateness, and how do you control it?

Allowed lateness holds window state past the point where the window would normally be released. Concretely, with a 1-hour window and 10 minutes of allowed lateness, you are holding roughly **1/6 of an hour's worth of accumulators** at all times instead of none. Multiply by the number of distinct keys, and that is your state footprint.

Two multipliers make it worse. **Key cardinality**: a window keyed by `user_id` with 50 million users holds 50 million accumulators. And **accumulator size**: a `CombineFn` whose accumulator is a list of every value seen (rather than a scalar) holds the entire group in memory, so lateness multiplies an already-unbounded structure.

The controls:

- Keep the accumulator O(1) per key — a scalar or a bounded structure, never "all values seen".
- Bound the key cardinality; consider a two-stage aggregation (coarse key first, fine key second) if you need both.
- Reduce `allowed_lateness` to the smallest value that covers your real lateness distribution — measure it from your data rather than guessing.
- Use `DISCARDING` accumulation where the downstream consumer does not need the running total; it releases the aggregate state between firings.

The production story: a session window with a 30-minute gap and 1 hour of allowed lateness, keyed by session id, on a workload with 200,000 concurrent sessions. The state estimate was 200,000 × ~4 KB ≈ 800 MB, comfortably above what the streaming workers were provisioned for. Workers were repeatedly evicted, the job thrashed, and processing latency climbed from 2 seconds to 40 seconds. The fix was a bounded accumulator plus reducing lateness to 5 minutes — the same numbers, an order of magnitude less state.
