# Interview Question Bank — Google Dataflow with Apache Beam

> **The question bank for this course.** Module files build the understanding;
> [top-50.md](top-50.md) is the final-night revision.

---

## What this bank is

This is a working interview bank for Dataflow and Apache Beam — not a
flashcard list, and not a set of definitions. Every question was selected
because the answer **changes what you build**, and every answer is written
the way a senior engineer who has actually run this in production would say
it out loud.

Each answer follows the same six-part structure:

1. **The direct answer**, in the first one or two sentences. No throat-clearing.
2. **The mechanism** — the internal Beam concept that explains it: the
   shuffle, fusion, state, watermark, coder, checkpoint, bundle, accumulator.
3. **When the alternative wins** — the trade-off and its boundary condition.
   "It depends" is never acceptable without saying what it depends on.
4. **A production failure story** — the actual symptom, and the fix.
5. **Code**, where it clarifies and nowhere else.
6. **Numbers** — vCPU-hours, dollars, row counts, latency, worker counts.

The failure story is the part interviewers probe. Anyone can recite that
`CombinePerKey` scales better than `GroupByKey`; a senior interviewer wants
to know whether you have *seen* it fail, and what the graph looked like when
it did.

### How the bank is structured

| File | Questions | What it covers |
|---|---:|---|
| [01-beam-fundamentals.md](01-beam-fundamentals.md) | 14 | PCollection, PTransform, PRunner; bundles, fusion, laziness; portability; batch vs streaming; Dataflow vs the rest |
| [02-core-transforms.md](02-core-transforms.md) | 16 | Map/FlatMap/Filter; `ParDo` and `DoFn`; `CombineFn` and combiners; `GroupByKey`, `CoGroupByKey`; side inputs |
| [03-io-and-coders.md](03-io-and-coders.md) | 14 | Sources and sinks; sharding; coder selection; BigQuery dispositions; schema evolution; multi-source patterns |
| [04-gcp-setup-and-runners.md](04-gcp-setup-and-runners.md) | 12 | The three service identities; IAM; billing and APIs; regions; the Direct Runner family; Prism; `PipelineOptions` |
| [05-templates-and-deployment.md](05-templates-and-deployment.md) | 14 | The Dataflow service; flex templates; SDK-version pinning; autoscaling; logs and metrics; cancelling a job |
| [06-batch-engineering.md](06-batch-engineering.md) | 14 | Filter-early and aggregate-early; shuffle joins vs side inputs; idempotency; determinism; DLQs; backfill |
| [07-streaming.md](07-streaming.md) | 16 | Event time; the watermark; triggers and lateness; accumulation modes; Pub/Sub delivery; state and timers; `TestStream` |
| [08-production-ops.md](08-production-ops.md) | 16 | The testing pyramid; custom metrics; autoscaling; the cost model; CMEK and VPC-native jobs; triage order |
| [top-50.md](top-50.md) | **50** | The highest-yield subset — read this the night before |

**Total: 166 questions.** The module files are arranged in the order the
course teaches the material; `top-50.md` is arranged by *interview theme*,
because that is how a conversation actually goes.

### How the bank maps to the chapters

| Module file | Primary chapters |
|---|---|
| `01-beam-fundamentals.md` | [01-what-is-apache-beam](../chapters/01-what-is-apache-beam.md), [02-architecture-and-portability](../chapters/02-architecture-and-portability.md), [03-pipeline-flow-and-the-runner](../chapters/03-pipeline-flow-and-the-runner.md) |
| `02-core-transforms.md` | [09-map-and-flatmap](../chapters/09-map-and-flatmap.md), [10-filter-and-flatten](../chapters/10-filter-and-flatten.md), [11-pardo-and-dofn](../chapters/11-pardo-and-dofn.md), [12-combineperkey-and-combiners](../chapters/12-combineperkey-and-combiners.md), [13-cogroupbykey-and-groupbykey](../chapters/13-cogroupbykey-and-groupbykey.md) |
| `03-io-and-coders.md` | [07-read-inputs](../chapters/07-read-inputs.md), [08-write-outputs](../chapters/08-write-outputs.md), [14-io-catalogue-and-coders](../chapters/14-io-catalogue-and-coders.md) |
| `04-gcp-setup-and-runners.md` | [06-sdk-setup-and-colab](../chapters/06-sdk-setup-and-colab.md), [19-gcp-project-billing-and-apis](../chapters/19-gcp-project-billing-and-apis.md), [20-service-accounts-and-bucket](../chapters/20-service-accounts-and-bucket.md), [21-direct-runner](../chapters/21-direct-runner.md) |
| `05-templates-and-deployment.md` | [24-dataflow-service-architecture](../chapters/24-dataflow-service-architecture.md), [25-creating-a-flex-template](../chapters/25-creating-a-flex-template.md), [26-executing-a-batch-job](../chapters/26-executing-a-batch-job.md) |
| `06-batch-engineering.md` | [04-batch-vs-streaming-and-the-model](../chapters/04-batch-vs-streaming-and-the-model.md), [28-executing-batch-to-bigquery](../chapters/28-executing-batch-to-bigquery.md), [50-case-study-custom-batch](../chapters/50-case-study-custom-batch.md) |
| `07-streaming.md` | [37-pubsub-architecture-and-io](../chapters/37-pubsub-architecture-and-io.md), [38-unbounded-collections-and-event-time](../chapters/38-unbounded-collections-and-event-time.md), [41-watermarks-and-allowed-lateness](../chapters/41-watermarks-and-allowed-lateness.md), [42-state-timers-and-processing-time-triggers](../chapters/42-state-timers-and-processing-time-triggers.md) |
| `08-production-ops.md` | [44-testing-beam-pipelines](../chapters/44-testing-beam-pipelines.md), [45-monitoring-and-autoscaling](../chapters/45-monitoring-and-autoscaling.md), [46-skew-hot-keys-and-reshuffle](../chapters/46-skew-hot-keys-and-reshuffle.md), [47-cost-model-and-optimization](../chapters/47-cost-model-and-optimization.md), [48-security-iam-and-cmek](../chapters/48-security-iam-and-cmek.md), [52-troubleshooting-and-common-failure-modes](../chapters/52-troubleshooting-and-common-failure-modes.md) |
| `top-50.md` | All of the above — selected for cross-layer coverage |

---

## The study plan

**A four-week plan for someone who knows Python and has seen Spark or
Flink.** If you have four weeks, do this. If you have two, compress weeks 1
and 2 and skip week 3's reading in favour of the module questions.

### Week 1 — The model and the transforms

Read [01-what-is-apache-beam](../chapters/01-what-is-apache-beam.md),
[02-architecture-and-portability](../chapters/02-architecture-and-portability.md)
and [03-pipeline-flow-and-the-runner](../chapters/03-pipeline-flow-and-the-runner.md).
Then work through the transform chapters: Map/FlatMap, Filter/Flatten,
ParDo/DoFn, CombinePerKey, CoGroupByKey/GroupByKey.

Run `project/batch_pipeline.py` on the Direct Runner. Break it on purpose:
add a duplicate transform label, remove a sink, feed it a malformed row.
See what the error says.

Then answer [01-beam-fundamentals.md](01-beam-fundamentals.md) and
[02-core-transforms.md](02-core-transforms.md) **out loud**. Not in your head —
out loud, standing up. If you cannot say the answer in two sentences, you do
not have the first half of it.

### Week 2 — Streaming

Read the event-time chapters: [04-batch-vs-streaming-and-the-model](../chapters/04-batch-vs-streaming-and-the-model.md),
[37-pubsub-architecture-and-io](../chapters/37-pubsub-architecture-and-io.md),
[38-unbounded-collections-and-event-time](../chapters/38-unbounded-collections-and-event-time.md),
[41-watermarks-and-allowed-lateness](../chapters/41-watermarks-and-allowed-lateness.md),
[42-state-timers-and-processing-time-triggers](../chapters/42-state-timers-and-processing-time-triggers.md).

Run `project/streaming_pipeline.py` with `--use-test-stream`, then with
`--trigger-count 5`, and watch the output change shape. Read
[07-streaming.md](07-streaming.md) and answer every question aloud.

### Week 3 — Operations, cost, and correctness

Read the GCP and operations chapters — project setup and billing, service
accounts, flex templates, monitoring and autoscaling, skew, the cost model,
security, troubleshooting. You do not need a GCP account for the questions;
you need to *understand* them.

Then read [03-io-and-coders.md](03-io-and-coders.md),
[04-gcp-setup-and-runners.md](04-gcp-setup-and-runners.md),
[05-templates-and-deployment.md](05-templates-and-deployment.md),
[06-batch-engineering.md](06-batch-engineering.md) and
[08-production-ops.md](08-production-ops.md), and answer them aloud.

This is the week most people skip, and it is the week that separates a
candidate who knows Beam from a candidate who has shipped on it.

### Week 4 — `top-50.md` and a mock interview

Read [top-50.md](top-50.md) **once, end to end**, in one sitting. Do not
write anything down yet. Notice which answers you could not produce.

Then go back and answer the ones you missed, out loud, writing down the
mechanism and the number if you can. Re-read only the answers you got wrong
or got vaguely right.

Finally, do a mock: pick 20 questions at random, set a timer for 90 seconds
per question, and answer each one **out loud** with the structure —
direct answer, mechanism, trade-off, failure story, number. The point of the
mock is not whether you know the answer; it is whether you can *get to* it
under pressure.

> **The honest advice:** `top-50.md` is for the final night. Reading it on
> day one is the single most common way people waste this bank. The module
> files are for building the understanding — they are slower, they repeat
> themselves, and they contain questions that will never be asked. That
> repetition is the point: it is what turns "I have read about the watermark"
> into "I know what happens when the slowest source stalls it."

---

## How to use the bank

**Do not memorise.** Memorised answers sound memorised, and a senior
interviewer can tell within two questions. What you are building is not
recall; it is the ability to *reason from a mechanism to a decision*.

**Write your own answer first.** Before you read the bank's answer, write
your own — three or four sentences, from memory. Then compare. You will find
one of three things:

- You knew it, and the bank adds a detail or a number. Good — you were
  nearly there, and the detail is worth keeping.
- You knew the shape but not the mechanism. This is the interesting case.
  Go back to the chapter and find the mechanism.
- You had the wrong model entirely. This is the most valuable outcome. Stop
  and re-read the chapter.

**Answer out loud.** Speaking is a different task from reading, and it is the
task the interview actually is. If you can only answer when you can see the
words, you have not prepared. The aim is: question → first two sentences
immediately, mechanism second, numbers third.

**Probe the failure story.** When you tell a failure story, ask yourself
"what was the symptom?" — a graph shape, a log line, a number that was
wrong, a bill. An interviewer who hears "it was slow" will not follow up.
An interviewer who hears "one worker at 100% CPU while 199 idled, and the
stage showed `MaxBundleDuration` in the hundreds of seconds" will ask three
good questions.

**Use the numbers.** The bank attaches numbers to most answers because
numbers are what distinguish an answer from a recital: O(keys) vs O(data),
$0.05–0.10 per vCPU-hour, 128 elements per bundle, 5 minutes of allowed
lateness, 1 TB. You do not need to memorise them exactly — you need to
*have* them, so that "it scales better" becomes "it keeps one accumulator
per key instead of buffering the whole group, so a 1 TB job runs on four
workers instead of failing".

**Revise by theme, not by file.** If you are weak in one area, read the
relevant `##` section of `top-50.md` and then go back to the corresponding
module file. Reading the bank front to back twice is less effective than
reading the weak section three times.

---

## What the interviewer is actually testing

Each theme in `top-50.md` probes a different mental model. Know which one
you are in, and you will know which details to lead with.

### "The model" — do you think in PCollections, or in scripts?

They are testing whether you reason about a **dataflow graph** or a sequence
of steps. A script-thinker asks "what is the next statement"; a
PCollection-thinker asks "what is the shape of this data and where does it
have to be materialised". The tell is what you do when the same PCollection
feeds three branches, and when the pipeline needs to fan out and re-join.
If your answer to "why did this not work?" is "the pipeline printed nothing",
you are still thinking in scripts.

### "Execution and the runner" — do you know what actually happens?

They are testing whether you understand that Beam is a **declarative graph
executed by someone else's engine**. The interesting answers are about
fusion, shuffling, bundling, checkpointing and the difference between
*semantics* (portable) and *execution* (not). A candidate who says "the
runner parallelises it" has not answered. A candidate who says "the runner
fuses my `Map` and `Filter` into one stage so nothing is written in between,
which is why adding a `Reshuffle` costs me a GCS round trip" is answering.

### "Transforms and combiners" — can you choose the right tool under scale?

They are testing **judgement about memory and shuffle cost**. The question is
never "what does `CombinePerKey` do" — it is "your job is now 40× larger,
what changes". The answer has to connect the choice of transform to a
memory bound, a shuffle volume, and a worker count. The common failure is
reciting the API without the cost model.

### "Windowing and streaming" — do you understand event time, or just the API?

They are testing whether you can reason about **a watermark that is a
consequence of your slowest source**, and about the difference between
"correct", "eventually correct" and "approximately correct". A candidate who
can explain why `AfterWatermark` plus allowed lateness is refused by Beam
— because Beam will not promise something it cannot prove — is operating at
a different level from one who lists trigger types.

### "Correctness and guarantees" — do you know what Beam does *not* promise?

They are testing honesty about **delivery semantics**. The trap is "exactly
once". The strong answer distinguishes at-least-once delivery from
exactly-once *state*, explains the checkpoint mechanism, and then says what
that means for your sink: it must be idempotent, and here is how to make it
so. Senior interviewers push here because it is where most production
outages live.

### "Dataflow operations and cost" — can you run and debug the thing?

They are testing **operational fluency**: what a job's graph tells you, what
a 403 on `storage.objects.get` actually means, what Dataflow bills for
(vCPU-hour, not bytes), and what a forgotten streaming job costs. These
questions are often asked by people who have never written the pipeline but
have paged you at 3 a.m. about it.

### "Design and trade-offs" — can you defend a decision?

They are testing whether you can **make and justify a choice** under
competing constraints. "We used `CoGroupByKey`" is not an answer; "we used
`CoGroupByKey` because the reference table was 4 million rows and a side
input would have copied it to all 200 workers, and the exactness requirement
ruled out an approximate join" is. Watch for the follow-up: they will ask
what you would do differently at 10× the data.

---

## A note on versions

This bank was written against **apache-beam 2.77** and **Google Dataflow as
of late 2026**.

The model, the transform semantics and the operational patterns in these
answers are stable across Beam versions, and the reasoning is what is being
tested. The **API details are not**: transform names, option flags, runner
names and default values do change between releases, and some things the
bank mentions have been tightened (an empty `AsSingleton` side input now
fails at pipeline construction rather than at run time; `beam.pvalue.AsSingleton`
is deprecated in favour of `AsDict`/`AsIter`/`AsList`).

So: **check every API detail against the SDK you have installed.** From the
course root:

```bash
.venv/bin/python -c "import apache_beam; print(apache_beam.__version__)"
.venv/bin/python -c "import apache_beam as beam; print(hasattr(beam, 'CombinePerKey'))"
```

The course's own linter does this for you across every chapter and project
file:

```bash
.venv/bin/python resources/audit_course.py
```

If a snippet in these answers does not match your installed SDK, the answer's
*reasoning* is still correct — but the code is not, and on an interview that
is the part that gets typed.

---

## Related material

- The course README — [../README.md](../README.md)
- One-page transform/trigger/flag reference — [CHEATSHEET.md](../resources/CHEATSHEET.md)
- The questions students actually ask — [FAQ.md](../resources/FAQ.md)
- The runnable pipelines — [project/](../project/)
