# The Course Project

A faithful, runnable simulation of the Google Cloud data platform. It
runs **locally with no GCP account, no credentials and no bill**, and
every number it prints is a number the chapters assert against.

---

## Why a simulation

Three reasons, in order of importance:

1. **You can learn the platform without a bill.** The service catalogue,
   the IAM policy engine and the cost model are all pure Python. You
   can explore a 34-service platform and a 23-role IAM policy on a
   laptop.
2. **The logic is testable.** Because `project/core/` imports nothing
   from Google Cloud, `pytest` runs 102 tests in about a third of a
   second. A test that needs credentials is a test nobody runs.
3. **Every claim in the chapters is checkable.** When a chapter says a
   partitioned scan is 100× cheaper, you can run it.

---

## Layout

```
project/
├── local_runner.py          # the console the labs run against
├── core/
│   ├── service_catalog.py   # 34 services, 12 regions, 8 categories
│   ├── iam_policy.py        # 23 roles, inheritance, conditions, explicit deny
│   ├── cost_model.py        # the pricing model for every service
│   ├── pipeline_logic.py    # the pure business logic
│   └── platform_sim.py      # the project, the resources, the runtime
└── tests/
    ├── test_pipeline_logic.py
    └── test_iam_and_cost.py
```

---

## Running it

```bash
# Generate the deterministic dataset (once)
python resources/sample_data.py --output-dir ./sample_data

# The pipeline
python project/local_runner.py --run

# The service inventory
python project/local_runner.py --services
python project/local_runner.py --categories

# Where each service is available
python project/local_runner.py --regions

# Who can do what
python project/local_runner.py --iam

# What it costs
python project/local_runner.py --cost
python project/local_runner.py --compare
```

---

## What the pipeline does

The stages map one-to-one onto GCP:

| Stage | Pure function | GCP equivalent |
|-------|---------------|----------------|
| Ingest | `ingest_events()` | Pub/Sub subscription pull |
| Validate | `validate_event()` | Dataflow `DoFn` / Dataproc `map` |
| Normalise | `normalise_event()` | Dataflow `Map` + a currency lookup |
| Aggregate | `aggregate_events()` | BigQuery SQL, or `CombinePerKey` |
| Publish | `publish_topic()` | Pub/Sub publish |
| Load | `build_bigquery_rows()` | BigQuery partitioned table load |

The windowing path — `bucket_by_window()` and `aggregate_by_window()` —
is the pure equivalent of a Dataflow fixed window. The bucket is derived
from the **event timestamp**, never from arrival time.

### The dead-letter path

`validate_event()` returns a stable, low-cardinality reason code rather
than a boolean. The 12 malformed rows in `sample_data/` cover every
reason the validator can emit, so the failure taxonomy is *testable*:

```text
bad_amount 1 · bad_timestamp 1 · missing_event_id 1 · missing_user_id 1
negative_amount 1 · unknown_channel 1 · unknown_currency 1
unknown_event_type 1 · unknown_region 2 · wrong_field_count 2
```

A reason code becomes a metric label and a partition key. A raw
exception message never should.

### Idempotency

The dedup key is derived from the data:

```python
def dedup_key(event_id: str, partition: str) -> str:
    return f"{partition}:{event_id}"
```

Never from arrival time. A load-time timestamp would make a retry
produce *different* rows rather than the same rows, which defeats
deduplication entirely — the classic reason a pipeline double-counts
after a failure.

---

## The IAM engine

`iam_policy.py` implements the real precedence rules:

1. An explicit **DENY** beats any ALLOW.
2. Otherwise, an **ALLOW** from any applicable binding wins.
3. A binding with a **condition** applies only when the condition
   matches the resource attributes.
4. Nothing matching means denied.

GCP resource paths are sequences of `type/name` pairs, and inheritance
steps in *pairs*:

```python
>>> ancestor_paths("projects/p/buckets/b/objects/o")
['projects/p/buckets/b/objects/o', 'projects/p/buckets/b', 'projects/p']
```

Note what is absent: `projects/p/buckets/b/objects` and
`projects/p/buckets`. Those are not real GCP scopes — there is no such
thing as an IAM binding on "the objects collection of a bucket" — and
treating them as scopes makes a policy look like it inherits grants it
does not.

```python
>>> from iam_policy import Policy, Principal, Binding, evaluate
>>> policy = Policy()
>>> policy.add(Principal("user", "ana@example.com"), Binding("roles/storage.admin"), "projects/p")
>>> evaluate(policy, "ana@example.com", "storage.objects.get", resource="projects/p/buckets/b").allowed
True
```

---

## The cost model

`cost_model.py` implements each pricing *model* faithfully — per-TB
scanned, per-vCPU-hour, per-GB-stored with a retrieval charge.

```python
>>> from cost_model import compare_architectures
>>> for name, cost in compare_architectures(scanned_tb=1.0):
...     print(f"{name}: ${cost:.4f}")
Streaming on Dataflow: $0.0000
Spark on Dataproc: $0.0000
Batch on BigQuery (partitioned): $0.0625
Batch on BigQuery (unpartitioned): $6.2500
```

The comparison is the point: a partitioned query costs a hundredth of
the unpartitioned one, which is why *the cheapest streaming architecture
is usually the most expensive batch architecture* once you price the
compute correctly.

Note the two `$0.0000` rows. They are free only because the comparison
passes `streaming_hours=0` — a Dataflow pipeline that runs continuously
is billed every hour it is alive, and that is the number that decides
whether streaming is worth it. The function takes `streaming_hours` for
exactly this reason; never read a `$0.00` streaming row as "free".

---

## Running the tests

```bash
python3 -m pytest project/tests/ -q
```

102 tests, no cloud SDK required, no network access, no credentials.
They cover the validation rules, the windowing, the partitioning, the
idempotency guarantees, the IAM precedence rules and the cost model.

---

## Extending it

The modules are deliberately small and independent. A natural next step
is to add a second project to `platform_sim.py` — a streaming variant
with a service account that cannot delete data — and watch the IAM
engine refuse the delete. That is the fastest way to internalise the
model.
