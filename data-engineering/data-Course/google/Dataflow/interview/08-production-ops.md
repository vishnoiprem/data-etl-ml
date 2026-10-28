# Module 8 — Production Operations

> **16 questions · Module 8 · Production Operations**

---

## Testing

### 1. What is the testing pyramid for a Beam pipeline, and where does each layer sit?

Four layers, from cheapest to most expensive:

1. **Pure-function unit tests.** Parse a line, convert a currency, apply a filter predicate. No Beam at all, milliseconds per test, 90% of your coverage should live here. The course's `project/tests/test_transforms.py` is this layer — 51 tests with no Beam required.
2. **Transform-level tests.** Build a small pipeline with `beam.Create` and assert on the output. Seconds per test. This is where you test `CombineFn` behaviour, joins, and filters.
3. **Pipeline-level integration tests.** Run the whole pipeline on a fixture file end to end, using `TestPipeline`. Tens of seconds. The course's `TestBatchPipeline` class is this layer.
4. **Template and deployment tests.** Launch the actual flex template against a small staging dataset and assert on the output. Minutes, and it needs GCP. Most teams skip this and regret it.

The ratio that works is roughly 60/25/10/5. The failure mode to avoid is the inverse — most teams write only layer 3, so a one-character change to a parser costs a full pipeline run, and the test suite is too slow to run on every commit.

### 2. What is `TestPipeline`, and why is the older `PTest` style deprecated?

`TestPipeline` is a `Pipeline` subclass that runs itself when the context manager exits, with assertions attached via `assert_that`. It replaced the older `PTest` pattern, where you built a pipeline and then called `p.run()` and asserted on the result object manually.

The reasons `PTest` is deprecated are practical, not aesthetic. `TestPipeline` ties the assertion to the pipeline's lifetime, so a failed assertion fails the test rather than surfacing as a `RuntimeError` from a result object you forgot to check. It also handles the runner selection and the `+inf` watermark evaluation that closes out a streaming run in the test environment.

There is a second, sharper reason specific to this course: the `PTest` API and the modern one have *different semantics* around how the pipeline is finalised, and mixing them produces tests that pass locally and behave differently on Dataflow.

One gotcha worth stating: `TestPipeline` reads its runner from the `BEAM_RUNNER` environment variable when it is not given one explicitly. The course's `conftest.py` sets `BEAM_RUNNER=BundleBasedDirectRunner` for the whole session, which is why the Prism runner's panic on `AfterWatermark` never appears in the test suite.

### 3. Why does `use_global_window=False` change the element type, and what breaks if you ignore it?

When you assert on a windowed `PCollection`, Beam hands you `WindowedValue` objects, not the bare values. A `WindowedValue` carries a value, a timestamp, and a window (with a start and an end). Comparing those directly against plain tuples fails, and the error message is unhelpful — something like "expected [('EMEA', 3)] but got [WindowedValue(...)]".

The fix is either to write a window-aware matcher that unwraps `.value`, as `_windowed_values` does in `project/tests/test_pipelines.py`:

```python
def _compare(actual):
    unwrapped = [item.value if hasattr(item, "value") else item for item in actual]
    return sorted(unwrapped, key=repr) == sorted(expected, key=repr)
```

...or to pass `use_global_window=False` and use a matcher that understands the windowed type. The important discipline is that `use_global_window=True` (the default) is only correct when the pipeline genuinely uses the global window. Applying it to a windowed collection silently compares the wrong things — and if the windows differ, it may compare equal when the business answer differs.

A subtle point the course's matcher makes explicit: it deliberately does **not** check the window boundaries. That is usually correct — the test is about *how many firings happened and what each contained* — but it means a test will not catch a window that is offset by an hour. If window boundaries are what you care about, assert on them explicitly.

### 4. How do you test a `CombineFn` directly, and why is that better than testing it through a pipeline?

Test the combiner as a plain object, with no pipeline at all. Call `create_accumulator`, `add_input`, `merge_accumulators` and `extract_output` yourself. It takes microseconds and it isolates exactly the property you care about.

The most valuable property test is **merge-order independence**: build two accumulators from disjoint halves of the input, merge them in both orders, and assert the outputs are identical. The course does exactly this:

```python
left = combiner.create_accumulator()
for order in orders[:2]:
    left = combiner.add_input(left, order)
right = combiner.create_accumulator()
for order in reversed(orders[2:]):
    right = combiner.add_input(right, order)
merged = combiner.merge_accumulators([left, right])
assert combiner.extract_output(merged) == {"order_count": 3, "revenue_eur": 60.0}
```

Why this matters more than any pipeline test: the runner merges partial accumulators from different workers **in an arbitrary order**. A combiner whose merge is order-dependent produces different totals on different runs, and it produces them *correctly* according to the code. A pipeline-level test would only catch this on a run where the scheduler happened to split the work differently.

Also test the empty accumulator: `extract_output(create_accumulator())` must return a sensible zero rather than raising. A combiner that divides by count, or takes `accs[0]`, will pass every "happy path" test and fail the first time a key has zero rows.

### 5. What custom metrics should a production Beam pipeline emit, and why not just rely on the built-in counters?

The built-in counters (`ElementCount/in`, `ElementCount/out`, `ElementCount/estimated`) are necessary but not sufficient — they tell you the shape of the data flow, not whether it is *correct*. Add your own counters for the business-critical quantities, and use `beam.metrics.Metrics` to do it.

The ones worth emitting: rows rejected by a filter (so the DLQ count is visible without querying GCS), rows per source, rows per output partition, the number of distinct keys after aggregation, and the total value of a monetary aggregation. These are the numbers you would otherwise have to query the output for — which is slow and, for a streaming job, impossible after the fact.

The mechanism is a counter object:

```python
from apache_beam.metrics import Metrics

class CountFilterFn(beam.DoFn):
    def process(self, element):
        Metrics.counter('ingest', 'rejected').inc()
        yield element
```

The production payoff: a pipeline that emitted a `rejected` counter and alerted on it caught a source-schema change within minutes, because the rejection rate went from 0.02% to 18%. Without it, the only signal was a downstream total that was quietly 18% low, which surfaced three weeks later.

### 6. What is the difference between `Basic` and `Aggressive` autoscaling, and when does each one win?

`Basic` scales roughly one worker per 1.5× the current CPU target and is deliberately slow to react. `Aggressive` targets ~85% utilisation and scales up quickly, but can oscillate: it adds workers, utilisation drops below the target, it removes workers, the backlog returns, and it adds them again.

`Aggressive` wins when latency matters more than cost: a streaming job with a sub-10-second freshness requirement, or a batch job on a deadline. `Basic` wins when you are cost-constrained and the workload is steady — overnight batch jobs typically.

For batch specifically, the right answer is usually neither: use `--num_workers` with `--autoscaling_algorithm=NONE`. A batch job's total cost is roughly `workers × runtime`, and autoscaling spends part of that runtime scaling. On a job that processes 1 TB, choosing 50 workers when 30 would do is a 40% overspend.

The concrete failure: a streaming job on `Aggressive` with `--max_workers=100` that scaled between 3 and 12 workers every few minutes, burning ~30% of its vCPU-hours on provisioning and teardown, and still missing its freshness SLO during the ramp. The fix was `Basic` with a lower ceiling and a larger machine type.

---

## Monitoring and cost

### 7. What does Dataflow actually bill for, and what does it not?

Dataflow bills **vCPU-hour for worker time**, not bytes, and not "jobs". A worker running for one hour on `n1-standard-4` (4 vCPUs) costs roughly 4 vCPU-hours, at approximately **$0.05–0.10 per vCPU-hour** depending on region and commitment — so about **$0.20–0.40 per worker-hour**. Streaming adds a per-GB charge of roughly **$0.01–0.02 per GB processed**; batch is cheaper per vCPU-hour but you still pay for the shuffle in GCS and, most expensively, for BigQuery.

The mental model that actually predicts the bill: **what is running, for how long**. Idle workers cost the same as busy workers. A job that reads 10 MB and finishes in 20 seconds costs almost nothing; a job that reads 10 MB and runs for 3 hours because it is streaming and has a hot-shuffle stage costs a lot.

The corollary surprises people: Dataflow is *not* primarily a data-volume cost. Moving 10 TB through a well-tuned batch job may cost less in Dataflow than in BigQuery, because the Dataflow bill is time-based and the BigQuery bill is scan-based. Conversely, a streaming job processing 5 GB/hour for a month costs ~$180–360 in per-GB charges alone, plus the worker time, on data that is almost certainly too small to justify streaming.

### 8. What happens when a streaming job is left running — and how do you prevent it?

It keeps paying for its workers, whether or not it is doing anything. A three-worker `n1-standard-4` streaming job left up for 30 days costs roughly 3 × 4 × 720 × $0.05–0.10 ≈ **$430–860** in worker time, before the per-GB charge. At twenty workers it is five figures a month for a pipeline nobody is reading.

Prevention, in layers:

1. **Budget alert at $1** — the cheapest possible insurance, and `resources/SETUP.md` sets exactly this.
2. **A scheduled sweep** that lists streaming jobs older than a TTL and cancels them. `gcloud dataflow jobs list --filter="state:JOB_STATE_RUNNING"` is the query.
3. **Pipeline name TTL.** When you cancel a job you still need to release the name for redeployment; `gcloud dataflow jobs cancel JOB_ID` leaves the name reserved. That is what `--now` on the pipeline name is for.

The trap that compounds the bill: cancelling the job does not stop the subscription accumulating messages. When you restart, every accumulated message is delivered, so the "quick restart" processes a backlog that may be days old — more per-GB charges, and possibly a state explosion on the streaming side.

### 9. How do you detect skew in a Dataflow job, and what are the two fixes?

Skew is when one key has far more data than the others, so one worker gets all the work while the rest idle. The symptom is a job where worker CPU is wildly uneven, one stage takes far longer than its peers, and the job's wall-clock time is dominated by a single stage.

Detect it from the **execution graph** and the per-worker metrics: `gcloud dataflow jobs graph show JOB_ID --format=json` shows the fused stages and their per-stage timings, and the worker logs show how long each bundle took. A stage whose `mean_processing_time` is 50× its neighbours is the fingerprint. On the Dataflow UI the same signal appears as "hot keys" in the shuffle stage.

The two fixes, with different mechanics:

- **Hot key splitter.** Manually split a hot key into N sub-keys (for example, `key + "_" + random(0, N)`), aggregate each, then re-merge the N partial results. This works when the *value* of the hot key is large but you only need the final aggregate. It requires a second aggregation stage to recombine, which is the cost.
- **`Reshuffle`.** `beam.Reshuffle()` breaks fusion and forces the runner to redistribute data across workers. It helps when the skew comes from fusion creating a single hot step, or when you need a barrier between stages. It does **not** fix genuine key skew — if one key owns 80% of the data, no amount of redistribution makes that key smaller, because the key is atomic. It only ensures the *non-skewed* work is spread evenly.

The production case: a pipeline counting events by `session_id` where one test account generated 40% of the traffic. The job ran 4 hours; the same data with a hot key splitter took 35 minutes. `Reshuffle` alone had done nothing, which is the point worth making in the interview.

### 10. What are CMEK and VPC-native jobs, and why do they matter?

**CMEK** (Customer-Managed Encryption Key) means you supply the key that encrypts your data at rest. Dataflow's default is Google-managed encryption; CMEK gives you the key, the rotation policy and the revocation. It matters when a compliance regime requires you to be able to prove who could have read the data, or when you need the key to survive a project deletion. The cost is that you must also manage the key's lifecycle — a disabled CMEK key makes every running job using it fail.

**VPC-native (private IP) jobs** run the workers inside your VPC without external IP addresses, so worker-to-service traffic (GCS, BigQuery, Pub/Sub) stays on the Google network and is not exposed to the public internet. It matters for anything touching sensitive data, and it is a prerequisite for some compliance baselines. The operational costs are real, though: the VPC must have Private Google Access enabled on its subnetworks, the region must have Private Service Connect endpoints configured, and you will spend time on DNS and routing.

The trap with CMEK: the key region and the job region must match, and the key's location cannot be changed. Rotating a key is easy; moving it across regions means recreating the job.

---

## Security and troubleshooting

### 11. How do you pass secrets to a flex template without leaking them?

First: **do not pass secrets as template parameters**. `--parameters` values appear in the job's metadata, in `gcloud dataflow jobs describe`, and in Cloud Logging. A password in a parameter is a password in your audit trail.

The right mechanisms, in order:

1. **Secret Manager**, with the worker service account granted `roles/secretmanager.secretAccessor` on the specific secret. The template reads it at runtime via the `google-cloud-secret-manager` client. Access is scoped to that one secret, and every read is logged in Secret Manager's own audit trail.
2. **Service account impersonation** for the actual GCP calls — the worker runs as a dedicated service account with the minimum roles, as `resources/SETUP.md` sets up, and it never has a downloadable key.
3. **Environment variables set from Secret Manager at job start** for libraries that need them — still fetched at runtime, never persisted in the job parameters.

The trap people fall into is putting the secret in a **custom container image** as an `ENV` or in a baked-in config file. The image is readable by anyone with `storage.objects.get` on the registry, and it persists in every layer forever. I have seen a production secret rotated out of emergency because it had been baked into an image that could not be rebuilt.

Also: the *submitting* identity and the *worker* identity are separate. A template that reads a secret using the submitter's credentials will fail on the worker, because the worker does not have them — the worker service account needs its own accessor role.

### 12. What is the standard triage order when a Dataflow job fails?

A fixed order, so you do not waste time:

1. **Get the state and the reason.** `gcloud dataflow jobs describe JOB_ID --format=json'` and look at `status.state` plus `status.state.message`. "The job failed because a worker encountered an error" is the unhelpful default; the real message is in `status.userMessage` sometimes, but often not at all.
2. **Get the worker logs.** `gcloud logging read "resource.type=cloud_dataflow_job AND resource.labels.job_id=JOB_ID AND severity>=ERROR" --limit=200`. This is where the Python traceback is. The job-level summary almost never contains it.
3. **Distinguish *submit* failure from *run* failure.** If the job never reached `JOB_STATE_RUNNING`, the problem is IAM, the staging location, the API enablement, or the quota — not your pipeline code. If it ran and then failed, it is your code, your data, or an environment problem.
4. **Check the execution graph.** `gcloud dataflow jobs graph show JOB_ID --format=json` shows how far it got and which stage was executing. If it died in stage 3 of 9, everything after stage 3 is irrelevant.
5. **Check the metrics.** `gcloud dataflow jobs describe JOB_ID --format='value(metrics)'` — the per-stage `ElementCount` tells you whether it read any input at all. Zero input elements means the source failed, not the processing.

The order matters because the most common time-waster is debugging the Python code when the job never started. A 403 on `storage.objects.get` at submission time looks exactly like a crash if you skip straight to the logs.

### 13. What are the most common Dataflow error messages, and what do they really mean?

| Message | Real cause |
|---|---|
| `RuntimeError: Transform name is already used` | Two transforms in the same pipeline share a label. The message does not say which — check the labels yourself. |
| `ValueError: Unsafe trigger: AfterCount(100) may lose data` | An unsafe trigger without `--allow_unsafe_triggers`. |
| `ValueError: accumulation_mode must be provided for non-trivial triggers` | `AfterCount`/`AfterWatermark` without `accumulation_mode`. |
| `403 storage.objects.get` | The Dataflow **service agent** lacks `roles/storage.objectAdmin`. If the agent already existed, remove and re-add the binding — Dataflow caches the policy at creation time. |
| `DefaultCredentialsError: Could not automatically determine credentials` | No Application Default Credentials. Run `gcloud auth application-default login`. |
| `AttributeError: module 'apache_beam.transforms.combiners' has no attribute 'Sum'` | There is no `beam.combiners.Sum`. Use `beam.CombinePerKey(sum)`. |
| `AttributeError: 'PipelineOptions' object has no attribute 'region'` | `region` lives on `DataflowOptions`; use `options.view_as(DataflowOptions)`. |
| `panic in ElementManager.Bundles watermark evaluation` | The Prism `DirectRunner` plus `AfterWatermark`. Use `BundleBasedDirectRunner`. |
| `RuntimeError: Transform name is already used` after a refactor | A label copy-pasted into a second branch of an `if/else`. |
| `KeyError` in a `GroupByKey` stage | `GroupByKey` on a non-`KV` element. |
| `TypeError: unhashable type: 'dict'` | A dict used as a key. Use a tuple. |

The pattern worth calling out: most of these are **construct-time** failures — Beam validates the graph before launching anything — so they fail in seconds, not minutes. The expensive ones are the IAM and quota errors, which fail at job creation after minutes of waiting, and the data errors, which fail wherever the bad row happens to be.

### 14. What do you check when a Dataflow job produces zero rows?

Work from the stages inward, and check the graph before the code.

1. **Did it read anything?** `ElementCount/in` for the read stage. Zero means the source was empty, the path was wrong, or the glob matched nothing. `WriteToText` with a `gs://` path and no matching files produces an empty result, not an error — a classic silent zero.
2. **Did a filter eat everything?** Compare `ElementCount/in` and `ElementCount/out` per stage. If the read produced 10 million and the next stage produced zero, the filter is the suspect. Check the predicate's *type* assumptions: a status field that is now lowercase, a numeric field that is now a string, a date format that changed.
3. **Was the key type right?** A `GroupByKey` on a `KV` where the key is `None` from a failed lookup groups everything under `None` — one group, one output row, and you were looking for thousands.
4. **Did a window never fire?** In streaming, a window with a watermark that never advances produces zero output and no error. Check `--idle_timeout` and the watermark.
5. **Did the sink write somewhere you are not looking?** `WriteToText` with `num_shards=N` writes `prefix-00000-of-000NN` files. If you `cat gs://bucket/out` you see the *directory*, not the content. And with `shard_name_template=""` the files are named differently.

The single most common cause, by a distance, is **the read matched nothing** — a typo in the path, a date-partition suffix that changed, or a `gs://` prefix that was omitted so the path was interpreted as local.

### 15. What does `WriteToBigQuery` idempotency look like in practice, and how do you pick a disposition?

The `write_disposition` controls what happens to existing rows in the target:

- **`WRITE_APPEND`** — append. New rows only. Duplicates on a re-run; use it only for genuinely append-only streams where you can dedup downstream.
- **`WRITE_TRUNCATE`** — replace the target (table or partition) with the job's output. This is the **idempotent** choice for a full overwrite, and it is what makes a re-run safe.
- **`WRITE_EMPTY`** — write only if the target is empty. Good as a guard against accidental double-runs, and useful for "first writer wins" pipelines.

`create_disposition` is separate: `CREATE_IF_NEEDED` creates the table if it does not exist (the normal choice), `CREATE_NEVER` fails if it does not (good for enforcing a contract with an existing table).

The production-relevant detail is that **`WRITE_TRUNCATE` truncates the whole target unless the target is a partition decorator**. So `project.dataset.table` truncates everything; `project.dataset.table$20260115` truncates only that day. A backfill that truncates the undecorated table deletes months of data — the mistake that ends careers.

The right pattern for a partition-scoped pipeline: derive the partition from the *event* timestamp, write to `table$<partition>`, use `WRITE_TRUNCATE`, and `CREATE_IF_NEEDED`. That makes a re-run of any day safe and independent.

### 16. What is the single most useful operational habit for running Beam on Dataflow?

**Make every job's output verifiable by a number, not by a green checkmark.** A job that reports `JOB_STATE_DONE` has only proven that it did not crash — not that it produced the right rows. Every pipeline should emit, and every dashboard should show, the input row count, the output row count, the rejection count and the primary aggregate. Then "did tonight's job work?" becomes a query, not an investigation.

The corollary habit is to **make the output idempotent so that the answer to "should I re-run it?" is always yes**. A non-idempotent sink creates a job that people are afraid to touch, and fear-driven operations are where outages come from.

The failure story: a nightly revenue job ran for six months with a `Filter` that silently dropped every row where `region` was null. The job was green every night. The null regions came from a partner's schema change on day three, and nobody noticed for six months because the only signal was "the job succeeded". A count assertion — `assert_that(output, equal_to(expected_count))` in the test, and a row-count comparison in production — would have caught it on day four.

The two habits together — verifiable numbers and idempotent outputs — are what turn "it ran" into "it produced the right answer, and you can safely run it again".
