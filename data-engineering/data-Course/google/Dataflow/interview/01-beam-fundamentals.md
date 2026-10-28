# Module 1 — Beam Fundamentals & Model

> **14 questions · Module 1 · Beam Fundamentals & Model**

---

## The model

### 1. What are the three core abstractions in Beam, and what breaks if you get one of them wrong?

**PCollection** (the data), **PTransform** (the operation), **PRunner** (the executor). A PCollection is an immutable, lazy description of a distributed collection; a PTransform takes one or more PCollections and produces one or more PCollections; a PRunner takes the graph and executes it.

Get the *lazy* part wrong and you write a pipeline that "does nothing". A PCollection is a description, not a dataset — building the graph performs no I/O, and every transform returns a new PCollection rather than mutating the old one. The classic symptom is a pipeline that exits cleanly having produced nothing because the branch you built was never consumed by a sink. Nothing raises; there is just no output file, and you spend twenty minutes looking for a bug that does not exist.

The failure that costs real money is getting the *immutable* part wrong. Because a PCollection cannot be mutated, you can safely feed the same one into five branches, and the runner will decide whether to read the source once or five times. Engineers coming from Spark reach for `.cache()` and then mutate a `Dataset` in place, and the second mutation silently invalidates the first branch's result.

The mechanism that ties all three together: at `run()`, Beam translates the graph into the **Runner API proto** — serialising each `DoFn` into a `ParDoPayload`, assigning a coder to every PCollection, attaching windowing strategies — and hands that to the runner's SDK harness. That proto is the real contract between SDK and runner, and it is why the same code runs on four engines.

### 2. What is a bundle, and why does the number of bundles matter more than the number of workers?

A **bundle** is a chunk of data processed as a unit — the runner's unit of parallelism, checkpointing, and retry. The runner calls `split_into_bundles` to partition a PCollection into bundles; each bundle is handled by one worker, checkpointed independently, and retried independently if it fails.

Bundle count, not worker count, is the ceiling on parallelism. If a source yields 10 bundles and you provision 100 workers, 90 of them sit idle and you pay for them anyway, because Dataflow bills vCPU-hour. Dataflow's default size hint is roughly 64 MB per bundle, so a 1 TB input yields on the order of 15,000 bundles — plenty. The pathological case is the opposite: one giant file that cannot be split. Beam cannot split a compressed file, so a single 50 GB gzip is one bundle, and it runs on exactly one worker no matter how large your cluster is. The fix is to split the input at the producer, not to add workers.

Two other consequences ride on the bundle. First, **retry granularity**: a failed bundle is retried without redoing the successful ones, so a worker that dies 90% of the way through a batch job does not cost you the whole job. Second, **memory bounds**: because a bundle is bounded, a streaming pipeline processes an unbounded stream in bounded memory.

The production symptom of too few bundles is a job that takes as long as one worker takes to process everything, with 99 workers idle. The metric to look at is the per-stage `mean_processing_time` versus the bundle count in the job graph.

### 3. What is fusion, and exactly where does it stop?

Fusion is the runner merging adjacent steps into a single processing step so the intermediate result is never written to storage. It is the runner's optimisation, not yours — you get it for free by expressing work in the Beam model, and you lose it the moment you drop to a runner-specific API.

Fusion applies when a step's output is consumed by exactly one downstream step and the intermediate can stay in memory. The textbook case is `Map` → `Filter` → `Map`, which fuses into one step. On a 1 TB intermediate, that is the difference between a 10-minute job and a 40-minute job.

Fusion stops at these barriers:

| Barrier | Why |
|---|---|
| `GroupByKey` | the shuffle boundary — keys must be co-located, so the intermediate is materialised |
| `CombinePerKey` with a non-liftable `CombineFn` | partial accumulators must be merged across workers |
| `CombinePerKey` with a liftable combiner (`sum`, `min`) | can usually be lifted into the upstream step, because the operation is associative and order-independent |
| Side inputs | a broadcast — every worker needs the whole thing, so it cannot be an in-memory handoff |
| `Reshuffle` | a deliberate barrier; this is the tool for breaking a fusion you do not want |
| `WindowInto` | changes the grouping semantics |
| A PCollection consumed by more than one step | the intermediate must be materialised so both consumers can read it |

The liftable/non-liftable distinction is the one worth internalising. `sum` is liftable: `(a + b) + c == a + (b + c)`, so you can accumulate incrementally upstream and get the same answer regardless of how the data was split. A combiner that subtracts an epsilon on each merge is not associative, cannot be lifted, cannot be fused, and gives different answers on different runners.

The failure story: a team added a `Reshuffle` "to spread the load" between a parse step and a `CombinePerKey`. It worked, but it silently disabled fusion of the whole chain upstream of it, and a nightly job went from 8 minutes to 55. They did not know fusion had been on the table. `gcloud dataflow jobs graph show JOB_ID` returns the *execution* graph — the fused stages the runner actually built — and that is how you would have caught it.

### 4. What is the watermark, in one sentence?

The watermark is Beam's estimate of how far behind the input's event time can still be — the point in event time beyond which no new elements are expected, and the signal that lets Beam decide a window is finished and fire its trigger.

Two corrections to the usual wrong answers. It is **not a clock**: it advances based on observed event timestamps, typically with a configured hold-back or from an idle-source heuristic, so it tracks the *data*, not the wall. And it is **monotonic**: it never moves backwards, which is why a late element that arrives after the watermark has passed its window is not retroactively inserted.

The mechanism is the runner's `WatermarkStrategy`. In a bounded (batch) pipeline, when the input is exhausted the runner advances the watermark to `+inf`, which closes every window and fires every `AfterWatermark` trigger — that is exactly why a batch pipeline produces the same windowed output as a streaming one, just all at once at the end.

The production failure: a streaming pipeline reads from two sources with different arrival patterns. The fast source advanced the global watermark past the slow source's data, so every element from the slow source was late and silently dropped by the trigger. The dashboard showed a complete-looking but understated revenue number, and nothing failed. The fix was a per-source watermark hold-back tuned to the slower source, plus an explicit late-data metric so "dropped" stopped being invisible.

### 5. What does Beam guarantee about delivery — exactly once, at least once, or neither?

Beam guarantees **at-least-once** delivery at the source and the sink. It does not promise exactly-once end-to-end, because exactly-once is a property of the *runner's* checkpoint-and-commit protocol, not of the SDK, and Beam deliberately leaves it to the runner. The SDK expresses the same pipeline either way; what changes is the guarantee you get from the runner you picked.

Concretely: Pub/Sub delivers at least once, so the same message can arrive twice; the standard defence is `id_label`, which lets the source deduplicate by a message ID. Dataflow Streaming's checkpointing gives you effectively-once processing *within* the pipeline — state is checkpointed, so a worker failure replays from the last checkpoint rather than reprocessing everything. But the sink write happens outside that transaction, so a crash between "checkpoint written" and "sink committed" can duplicate the output. Spark's Structured Streaming is at-least-once for most sinks; Flink's checkpointing protocol gives exactly-once on its state but still depends on the connector for the sink.

The practical consequence: **never trust the delivery guarantee alone for a non-idempotent sink.** Write to BigQuery with `WRITE_APPEND` and you can get duplicate rows on retry. Either design the sink to be idempotent — partition-keyed outputs, a deterministic row ID, or a deduplicating merge — or use a sink that commits atomically with the checkpoint.

The failure story I have seen most: a nightly `WRITE_APPEND` into BigQuery that used a `CURRENT_TIMESTAMP()` default for a row's load time. A worker was preempted mid-bundle, the bundle was retried, and the rows landed twice with different timestamps. Because the timestamps differed, a downstream `GROUP BY order_id` produced double counts. The fix was to make the row identity deterministic — `order_id` plus the processing date — and to use `WRITE_TRUNCATE` on a partition, or a merge, rather than blind append.

### 6. Why is "batch is streaming whose input ends" more than a slogan?

Because it is a statement about the watermark, and the watermark is what determines when windows close and triggers fire. In a streaming pipeline, the watermark advances as data arrives; in a batch pipeline, when the bounded input is exhausted, the runner advances it to `+inf`. Every window closes, every `AfterWatermark` trigger fires, and the batch pipeline emits the same windowed output as the streaming one — it just does it all at once, at the end, instead of incrementally.

This is the reason one Beam codebase can serve both modes. The business logic is written once; only the source and the windowing trigger change. A nightly hourly revenue rollup and a live revenue dashboard are the same pipeline with a different source and a different firing policy.

The practical value is testability. If batch really is streaming with an end, then you can *test* a streaming pipeline by giving it a bounded input, and you can *develop* it that way too. The course's local runs point the streaming pipeline at a finite NDJSON file; the watermark advances to `+inf` at the end and every window fires. That is a genuine equivalence, not an approximation — and it is also exactly the code path that makes the Prism runner panic, because Prism's `+inf` watermark transition is incomplete in Beam 2.77.

Where the slogan stops being true: it is a statement about *the model*, not about the operational profile. A batch job has a beginning, an end, and a predictable cost. A streaming job has none of those, and its per-element cost is dominated by checkpointing and state, not by the business logic. Two engineers who disagree about "are these the same pipeline" are usually arguing about the model while the disagreement that matters is about the cost model and the recovery story.

### 7. What is the difference between a lazy PCollection and a Spark RDD, and does it matter in practice?

A Beam PCollection is a *description of a dataset* that may not exist yet; a Spark RDD is a *handle to a distributed collection* that also may not be computed yet, but Spark's optimiser (Catalyst) owns the plan and you can see it. The practical difference is that in Beam the physical plan is opaque to you — the runner fuses and regroups steps, and you cannot see or influence the result. In Spark, `explain()` prints the plan and you can reason about physical properties like partitioning.

The second difference is time. Beam's event time is first-class: timestamps are carried on elements, windows and triggers are part of the portable model, and the watermark is a modelled concept. Spark's DataFrame API is processing-time by default; event time exists only in Structured Streaming, and it is a different API with different semantics. Flink goes the other way: event time and watermarks are native and central, but the batch and streaming APIs are separate — Flink's `DataSet` is a bounded stream in name only, and the operational model is genuinely different.

The third difference is state and the unit of work. Flink operators own keyed state and the runtime checkpoints it; Beam's state is a derived consequence of grouping, and checkpointing is the runner's problem. And the unit of parallelism differs: Spark's is a stage plus a shuffle; Beam's is the bundle.

None of this makes Beam better. Spark wins on iterative ML workloads with a mature, optimising engine and a far larger ecosystem. Flink wins on sub-second stateful streaming with native exactly-once. Beam wins when you want one codebase that runs batch and streaming on a managed runner, and when the runner is a commodity.

### 8. When would you choose Beam over Spark or Flink — and when would you not?

Choose **Beam** when the same logic must run in batch and streaming, when you want a managed runner that autoscaling and billing take care of, when you need to run the same graph on more than one engine, or when you want to hand off a pipeline without also handing off a cluster. Dataflow's autoscaling and per-second billing are the concrete wins.

Choose **Spark** when the workload is iterative ML (the GraphX and MLlib ecosystems, and Spark's whole optimisation story, are built for repeated passes over the same data), when the team already has a mature Databricks or EMR estate, or when you need SQL and DataFrame semantics rather than a PTransform graph. Spark's Catalyst optimiser and whole-stage codegen routinely beat Beam Python on tight per-element loops by a wide margin — roughly 2–5× is the usual figure for Java Beam over Python Beam, and Spark's codegen is a factor in that.

Choose **Flink** when you need genuinely sub-second stateful processing with native exactly-once and fine-grained control over keyed state and timers. Flink's checkpointing protocol is an engine property; in Beam, exactly-once is a capability a runner may or may not advertise.

Do not choose Beam because "it's Google" or "it's the Dataflow SDK". The Python SDK is slower per element than Java Beam, and Beam has no equivalent of Spark's Catalyst or Flink's native timer APIs in the same ergonomic form. Beam's real pitch is *portability of the graph plus a good managed runner*, and if you are only ever deploying to one managed runner, you are paying for portability you never use.

## Execution and the runner

### 9. How does Beam actually resolve the `--runner` flag?

Three steps, and the middle one is where the surprising failures live.

1. **Parsing.** Beam's own argparse layer parses `--runner DirectRunner` into `StandardOptions.runner` as a plain string. The course's `beam_options.build_options()` filters the argument list *before* Beam sees it, because `PipelineOptions` raises `SystemExit` on a flag it does not recognise, and pipeline scripts have their own flags (`--input`, `--output`) that Beam would otherwise reject.

2. **Defaulting and instantiation.** `Pipeline.__init__`/`run` reads `options.view_as(StandardOptions).runner`; if it is `None`, it uses `StandardOptions.DEFAULT_RUNNER`. If it is still a string, it calls `create_runner(name)`.

3. **`create_runner` lookup.** The lookup is **exact-match first, then `name + "runner"`**. So `--runner Direct` resolves to `DirectRunner`, and `--runner DirectRunner` resolves directly. If the resolved name contains no dot and matches nothing, you get `ValueError: Unexpected pipeline runner: Foo`.

Two traps. First, `beam.Pipeline(runner="DataflowRunner")` and `beam.Pipeline(options=options)` with `--runner DataflowRunner` land in the same place, but if you pass both a runner object *and* options whose `runner` differs, the constructor argument wins. Second, `--runner` is not the same as the runner's own class name in every case: in Beam 2.77 the plain name `DirectRunner` resolves to `SwitchingDirectRunner`, a dispatcher that picks Prism, FnAPI, or the bundle-based runner at submission time.

The production symptom of getting this wrong is silent: `SwitchingDirectRunner` falls back to the bundle-based runner when it sees a feature Prism lacks, and the only clue is a log line. A local run is 10× slower than expected and nobody knows why. Check the log for `Running pipeline with PrismRunner` versus `Pipeline failed on PrismRunner, falling back to DirectRunner`.

### 10. What is the Direct Runner family, and which one should you actually use?

Beam 2.77 ships several local runners and they are genuinely different engines, not aliases:

| Runner | Engine | Speed | Full trigger set |
|---|---|---|---|
| `BundleBasedDirectRunner` | pure Python, in-process | slow — roughly 1,000–10,000 elements/second for a simple `Map` | yes, everything |
| `SwitchingDirectRunner` | dispatcher; picks a specialist | depends on the pick | depends on the pick |
| `PrismRunner` | Go, via a local job server | 2–20× faster | no — panics on `AfterWatermark` |
| `FnApiRunner` | FnAPI worker model in Python | fast | batch only |

The plain name `DirectRunner` resolves to `SwitchingDirectRunner`, which visits the graph at submission time and picks Prism if the pipeline's features allow it, FnAPI otherwise, and the bundle-based runner as the final fallback. Prism is the interesting one: it is a Go implementation of Beam's *portable* runner, using the same Runner API proto and SDK-harness path as Dataflow, Spark, and Flink — which makes it the best local proxy for "will this work on a real cluster?".

Use `BundleBasedDirectRunner` for anything involving `AfterWatermark`, `userstate`, or session windows. That is why the course's `beam_options.py` sets `DEFAULT_RUNNER = "BundleBasedDirectRunner"`. Use Prism explicitly for fast local iteration on batch work — but expect a slow first run, because it downloads and caches a Go binary under `~/.apache_beam/cache/prism/`.

The failure story: the team switched the CI default to `DirectRunner` to make the suite faster. One pipeline in the suite used `AfterWatermark` against a bounded file. The watermark advanced to `+inf`, Prism's `ElementManager.Bundles` goroutine panicked while generating the final bundle, and the test failed with a Go stack trace that looked like a Beam bug rather than a runner-capability mismatch. The fix was to pin `--runner=BundleBasedDirectRunner` for that test.

The mechanism behind that panic is worth understanding. When a bounded input is exhausted the runner advances the watermark to `+inf`, which closes every window and fires every `AfterWatermark` trigger. In the bundle-based runner that is a normal, well-tested path. In Prism, the `ElementManager.Bundles` goroutine must generate a new *final* bundle for the affected stage so the window can be closed, and in the 2.77 release that generation path panics. Prism also lacks full support for `userstate` with real-time timers, deferred side-input combiners, and session windows — the switching runner's visitor checks for these and falls back when it finds them. Let `SwitchingDirectRunner` fall back automatically if you like, but read the log to know which engine actually ran: the fallback is silent.

### 11. What does `beam.Pipeline()` versus `p.run()` actually change?

They are equivalent in *when* the work happens — the context manager runs the pipeline when the block exits, `run()` runs it when you call it. The difference is the handle.

`with beam.Pipeline() as p:` gives you no result object. `p.run()` returns a `PipelineResult` with `state`, `metrics()`, `wait_until_finish()`, and `cancel()`. That handle is what you need when you want to inspect the job state, submit several pipelines from one process, submit and return (which is exactly what the Dataflow templates and flex templates do), or cancel a job in flight.

Two details that bite. First, **a `Pipeline` object is consumed by `run()`** — running the same pipeline twice raises. This is also why the switching runner can run your pipeline with Prism, fail, and run it again with the bundle-based runner without you ever seeing an error: both runs happen inside the single `run()` call.

Second, `run()` returns immediately; the work continues asynchronously. `wait_until_finish()` blocks until the pipeline reaches a terminal state, and `result.state` tells you which one. The context-manager form does block by default, unless you pass `--no_wait_until_finish`.

The production failure I care about: a script used the context-manager form and submitted a Dataflow job, then immediately tried to read the output prefix in GCS. Because the context manager waits until the job finishes, that part was fine — but the script had *also* wrapped the submission in a retry loop, and a job that failed logically (the BigQuery sink rejected rows after a schema change) triggered a retry that created a second, duplicate, billable job. The fix was to switch to `p.run()`, poll `result.state` with a timeout, and decide success from the output row count rather than from the exception.

## Portability

### 12. How portable is Beam, really — and where does the claim stop?

The portability claim is real at the **graph** level and bounded at the **configuration** level. The pipeline graph is portable; the deployment configuration is not. The rule of thumb is: if you want to run the same pipeline on Flink and Dataflow, you can — but you will use different flags for each, and some transforms are only available on one.

The mechanism is specific. Beam serialises the graph into the **Runner API proto**, and each runner implements an **SDK harness** that translates that proto into its own execution model. Flink translates Beam's windowing into Flink's native windowing, which is why Beam on Flink supports real stateful streaming rather than an emulation.

What breaks when you cross runners:

| Break point | Symptom |
|---|---|
| Runner-specific transform | submission fails: `Beam has not been implemented on this runner` |
| Runner-specific I/O | `ReadFromPubSub` exists only on Dataflow and the Direct runners |
| Unsupported coder | the runner cannot encode your type |
| Missing capability | the runner rejects a `requirements` entry in the proto |
| Windowing semantics | late-data and allowed-lateness behaviour differs subtly |
| Exactly-once | Dataflow streaming, Flink, and Spark offer different guarantees |
| Performance profile | the same graph has very different costs on different runners |

That last row causes the most disappointment. "It runs on both" is not "it performs the same on both". A pipeline that takes four minutes on Dataflow can take twenty on Dataproc because the shuffle profile is completely different.

The portability boundary also cuts through the SDKs. The Java SDK is closest to the metal — fastest and most complete. The Python SDK is the same model with roughly 2–5× lower throughput on tight per-element loops. Portability across SDKs means the *model* is the same, not that the performance is.

### 13. What does pinning the Beam SDK version in production actually buy you, and what does it cost?

Pinning buys **reproducibility of the execution environment**. It is the difference between "the pipeline that produced last quarter's numbers" and "a pipeline that might produce them again". Concretely, it pins coder defaults, `CombineFn` behaviour, trigger semantics, and the set of transforms that exist at all.

In practice the pin must happen in three places, and people usually remember one. The **worker image** (`apache-beam[gcp]==2.77.0` baked into the container) is the only true fix, because it makes the worker environment byte-identical to your test environment. The **requirements file** passed to the worker is second best — pip resolves and downloads on every cold start, adding 30–120 seconds per worker and producing version drift between workers if the constraint is loose. And your **local virtualenv** is third: it tells you what you developed against, which is not the same as what ran.

The cost is real and it is the usual reason pins get abandoned. Every pin is a maintenance obligation: security patches to Beam's dependencies, Python version support (Beam 2.77 does not support Python 3.14), and the slow drip of new features you now cannot use. The practice that works is to pin exactly, upgrade on a schedule rather than opportunistically, and keep a custom image so the pin is one `docker build` away from being changed rather than a resolution step away.

The failure story: a pipeline worked with Beam 2.60, was upgraded to 2.66 because a scan flagged a transitive dependency, and then a nightly job started writing one extra row per group. The change was in a default coder's handling of empty accumulators — not a bug fix, a behaviour change. Because the workers picked up a newer SDK than the one the code was tested against, the discrepancy showed up only in production. The fix was a custom image with the version pinned, plus a CI job that runs the pipeline on the exact image the worker will use.

## Dataflow versus the alternatives

### 14. Dataflow, Dataproc, or EMR — how do you choose?

**Dataflow** is a managed, serverless Beam runner. You write a Beam pipeline; Dataflow handles worker provisioning, autoscaling, and the shuffle. You pay for what you use, and the billing unit is **vCPU-hour** — not bytes scanned, not cluster uptime. Choose it when you want Beam semantics with no cluster to operate.

**Dataproc** is a managed Spark/Hadoop cluster. You pay for the cluster's wall-clock time whether or not the job is using it. Choose it when Spark is the requirement, when you need many jobs sharing a cluster, or when the workload is interactive and reuses the cluster across queries.

**EMR** is the AWS-managed equivalent of Dataproc. Choose it for the same reasons, if your organisation standardises on AWS and the Dataflow-in-AWS story (for example, a Beam runner or an equivalent managed service) is less attractive than a familiar Spark cluster.

The decision is usually not technical — it is which managed service your organisation already has, which identity and compliance boundary your data lives inside, and who operates it. The thing to be careful about is the billing model difference, because it changes how you optimise. Dataflow's per-vCPU-hour model means **idle streaming workers cost as much as busy ones**, and `max_workers` is a ceiling you pay down to, not a target you aim at. A Dataproc cluster costs the same whether it is running your job or sitting idle, so the calculus is "how long is the cluster up" rather than "how much capacity is provisioned".

There is a fourth option people forget: **do not use Beam at all** for the job. A `bq query` or a BigQuery scheduled query handles a straight SQL aggregation over a table for a fraction of the cost, in seconds, with no cluster and no pipeline. Beam earns its keep when there is parsing, stateful logic, multi-source joins, or streaming — not when the pipeline is a `GROUP BY` with a filter on top.

The billing model is what actually drives the choice, and it differs in a way that changes how you optimise. Dataflow bills **vCPU-hour**, not bytes scanned: a worker costs roughly $0.05–$0.10 per vCPU-hour, so a `n1-standard-4` worker is about $0.20–$0.40 per hour, plus a per-GB charge for streaming data processed. Dataproc and EMR bill the *cluster's* wall-clock time whether or not your job is using it. So on Dataflow, resident capacity and wall-clock time are the units, and a 10 MB input that autoscales to 100 workers can cost more than a 10 TB input that runs on one worker for an hour.

The levers on Dataflow follow from that: cap `--max_workers` at what the job actually needs (autoscaling starts at one worker), match `machine_type` to the work, filter before the `CombinePerKey` so fewer bytes cross the shuffle, avoid `GroupByKey` because it buffers whole groups and forces bigger workers, and use `--num_workers=1` with autoscaling off for small predictable batch jobs.

The failure story that sticks: a team left `--max_workers=200` on a streaming job and never revisited it. The job was fine, but a streaming job holds its workers whether or not data is flowing, so 3 workers of `n1-standard-4` left running for 30 days costs roughly 3 × 4 × 720 × $0.05–0.10 ≈ **$430–860** before any per-GB charge — and that is the *idle* case. The mitigation that worked was a scheduled sweep that cancels streaming jobs older than N days, plus a $1 budget alert. The related trap: cancelling the job does not cancel the Pub/Sub subscription, so messages accumulate while nothing is running and then arrive as a replay storm on restart.
