# The Datastream Project — Working Code

> The runnable part of the course. **Everything here works offline** — no GCP
> account, no credentials, no bill. The cloud paths are optional and clearly
> marked.

---

## What is in here

| File | What it does | Needs a cloud? |
|---|---|---|
| [`cdc.py`](cdc.py) | The merge engine. Pure stdlib. Implements every merge rule the course teaches. | **No** |
| [`cdc_pipeline.py`](cdc_pipeline.py) | CLI: read change events → apply the merge → write CSV + JSON + an audit log. | **No** |
| [`kafka_to_gcp.py`](kafka_to_gcp.py) | The Confluent path: parse Kafka messages, validate, build a parameterised INSERT, write to Postgres. | Only for the real DB write |
| [`cloud_function.py`](cloud_function.py) | The deployable Cloud Run / Cloud Functions handler. | Only when deployed |
| [`terraform/`](terraform/) | Datastream network config, source config, destination config, and stream. | Yes |
| [`tests/`](tests/) | 83 tests covering the merge, the Kafka parsing, the SQL generation, and the parameterisation guarantee. | **No** |

---

## The 60-second path

```bash
# From the course root
pip install -r project/requirements.txt

python resources/sample_data.py --output-dir ./sample_data

python project/cdc_pipeline.py \
    --input ./sample_data/changes.ndjson \
    --output ./out/customers \
    --merge-keys customer_id

pytest project/tests -q
```

Expected:

```text
  CDC replay summary
  ----------------------------------------------------
    events read          : 377
    rows in table        : 186
    changes applied      : 374
    events skipped       : 8
    skip reasons:
      delete_of_absent_row      : 2
      duplicate_insert          : 5
      missing_merge_key         : 1
```

```text
82 passed, 1 skipped
```

---

## `cdc.py` — the merge engine

This is the heart of the course. It is **pure standard library**, and that is
deliberate: the merge semantics are the hard part, and they must be testable
without a network, a credential, or a bill.

```python
from cdc import CdcState, apply_changes

state = CdcState(merge_keys=["customer_id"])
state.apply_events(events)     # events: list[dict]

state.rows                     # {("c000001",): {...}, ...}
state.applied_count            # 374
state.skipped_count            # 8
state.skipped_reasons          # {"duplicate_insert": 5, ...}
```

### The merge table it implements

| Event | Key present? | Result | Skip reason |
|---|---|---|---|
| INSERT | no | INSERT | — |
| INSERT | yes | converge | `duplicate_insert` |
| UPDATE | no | INSERT the after-image | `update_of_absent_row` |
| UPDATE | yes | UPDATE | — |
| DELETE | no | no-op | `delete_of_absent_row` |
| DELETE | yes | DELETE | — |
| any | key is null | skip | `missing_merge_key` |
| any | no row image | skip | `no_row_image` |

Every clause is an upsert or a delete **by key**. There is no clause that
appends — which is exactly why applying the same event twice has the same
effect as applying it once.

### The public API

| Function | Purpose |
|---|---|
| `ChangeEvent.from_dict(raw)` | Parse a raw change event into the dataclass. |
| `ChangeEvent.image_for_apply()` | The image to apply — `after` for INSERT/UPDATE, `before` for DELETE. |
| `CdcState.apply(event)` | Apply one event; updates the counters. |
| `CdcState.apply_events(raws)` | Apply a list of raw dicts. |
| `apply_changes(events, merge_keys)` | Convenience: build a state, apply everything, return it. |
| `build_bigquery_merge_sql(...)` | Emit the BigQuery `MERGE` with the `__op__` clauses. |
| `bigquery_create_table_sql(...)` | Emit the `CREATE TABLE` with `CLUSTER BY` and partitioning. |
| `iter_change_events(path)` | Stream change events from an NDJSON file. |
| `stream_events(...)` | A generator that yields events and counts them. |

---

## `cdc_pipeline.py` — the CLI

```bash
python project/cdc_pipeline.py --input CHANGES.ndjson --output PREFIX [options]
```

| Flag | Default | Meaning |
|---|---|---|
| `--input` | *required* | NDJSON file of change events |
| `--output` | *required* | Output prefix — `.csv` and `.json` are written beside it |
| `--merge-keys` | `customer_id` | Comma-separated merge key columns |
| `--audit` | none | Optional path for the change-event audit log |
| `--verbose` | off | Debug logging |

It writes three things:

1. `<prefix>.csv` — the destination table, one row per merge key.
2. `<prefix>.json` — the same rows, for a quick `jq`.
3. `<prefix>.audit.ndjson` — every event, with the skip reason if it was
   skipped. **This is the file that answers "what happened to that row?"**

### Try breaking it

```bash
# Merge on a non-unique column — the silent corruption.
python project/cdc_pipeline.py --input sample_data/changes.ndjson \
    --output out/by_region --merge-keys region

# A composite merge key.
python project/cdc_pipeline.py --input sample_data/changes.ndjson \
    --output out/by_region_tier --merge-keys region,tier
```

The second one produces *fewer* rows than the first, and the skip reasons
explain why: with `region` as the key, updates for one customer overwrite
another customer's row and the destination converges on the wrong value.

---

## `kafka_to_gcp.py` — the Confluent path

```bash
# Validate every message and report. No database.
python project/kafka_to_gcp.py --messages sample_data/transactions.ndjson --dry-run

# Write to a real PostgreSQL.
python project/kafka_to_gcp.py --messages sample_data/transactions.ndjson \
    --database-url postgresql://user:pass@localhost:5432/transactions
```

| Flag | Meaning |
|---|---|
| `--messages` | *required* — NDJSON file of Kafka messages |
| `--dry-run` | Validate and report without writing to a database |
| `--database-url` | PostgreSQL connection URL; falls back to `DATABASE_URL` |
| `--verbose` | Debug logging |

### The three stages

The function is deliberately three small pieces, in this order:

1. **Fetch the secret** — the database password from Secret Manager, cached
   in module scope. A rotated secret is not picked up until the instance
   restarts, which is fine for a database password and wrong for a
   short-lived token.
2. **Parse** — validate and flatten the JSON payload. It **raises** on a
   missing field rather than inserting a NULL, because a transaction with no
   amount is not a transaction with a zero amount.
3. **Insert** — a **parameterised** statement. The payload is data, never
   SQL.

### The parameterisation guarantee

```python
# build_insert_sql() returns 8 placeholders and never interpolates a value.
statement, values = build_insert_sql(row)
```

The test `test_a_quote_in_the_payload_stays_data` puts
`p0001'; DROP TABLE transactions; --` in the payload and asserts that
`DROP TABLE` appears in the **values**, never in the **statement**. That is
the difference between storing a string that contains a quote and executing
that string.

---

## `cloud_function.py` — the deployable handler

```bash
gcloud functions deploy ingest-transaction \
    --gen2 \
    --runtime python312 \
    --region us-central1 \
    --source project/ \
    --entry-point handle_event \
    --trigger-http \
    --no-allow-unauthenticated \
    --set-env-vars="INSTANCE_CONNECTION_NAME=PROJECT:REGION:INSTANCE,DB_NAME=transactions" \
    --set-secrets="DB_PASSWORD=db-password:latest" \
    --min-instances 1
```

Three things to notice:

- **`--set-secrets`, not `--set-env-vars`, for the password.** The secret is
  mounted at runtime and never baked into the image.
- **`--min-instances 1`.** A cold start lands on a real message otherwise,
  and the connector's offset does not advance until the function returns.
- **`--no-allow-unauthenticated`.** The sink connector authenticates; the
  function should not be open to the world.

### The status code contract

| Situation | Status | Connector behaviour |
|---|---|---|
| Malformed payload, validation failure | **400** | Skip (or route to the DLQ) |
| Database temporarily unreachable | **500** | Retry |
| Success | **200** | Commit the offset |
| Unexpected internal error | **500** | Retry |

---

## `terraform/` — the infrastructure

```bash
cd project/terraform
terraform init
terraform plan -var="project_id=YOUR_PROJECT_ID" \
               -var="region=us-central1" \
               -var="mysql_host=10.0.0.3" \
               -var="mysql_username=datastream_user" \
               -var="mysql_password=..." \
               -var='merge_keys=["customer_id"]'
terraform apply
```

| File | Contents |
|---|---|
| `main.tf` | Network config, IP allocation, MySQL connection + source config, BigQuery connection + destination config, and the stream. |
| `variables.tf` | Every input, with `merge_keys` defaulting to `["customer_id"]`. |
| `outputs.tf` | The stream name, the stream ID, and the IP allocation address. |

> The `mysql_password` variable is `sensitive = true`. Never commit a
> `terraform.tfvars` that contains it.

---

## `tests/` — what is covered

```bash
pytest project/tests -q
```

| File | What it asserts |
|---|---|
| `test_cdc.py` | Every row of the merge table; idempotency; the merge SQL and DDL generators; the skip counters. |
| `test_kafka_to_gcp.py` | Payload parsing, timestamp normalisation, the **parameterisation guarantee**, duplicate detection, and the secret fallback. |
| `test_pipeline.py` | The CLI end to end — file in, CSV and JSON out, the summary printed. |
| `conftest.py` | The fixtures, including a `FakeCursor`/`FakeConnection` that records the SQL so the parameterisation can be proven. |

The one skipped test is the Secret Manager path, which needs the SDK and
credentials installed.

---

## The one-line mental model

> The log is an immutable history. The destination is a projection of it.
> The merge key is the join between them — it must be unique, immutable and
> minimal. Everything else in this directory is an implementation detail of
> one side or the other.

---

## Related material

- The chapters — [../chapters/](../chapters/)
- The interview bank — [../interview/](../interview/)
- The setup guide — [../resources/SETUP.md](../resources/SETUP.md)
- The SQL — [../sql/](../sql/)
