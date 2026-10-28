# Module 3 — I/O & Multi-Source

> **14 questions · Module 3 · I/O & Multi-Source**

---

## Sources and sinks

### 1. How do you read a CSV with a header, and what goes wrong if you forget the header?

Use `beam.io.ReadFromText` with `skip_header_lines=1`, or read the raw lines and filter the header yourself. The header is a *row of data* to `ReadFromText` — it is not metadata, and Beam will happily parse it as a record. The course's `is_valid_order` returns `False` for the header row (it has no `order_id`), so the pipeline drops it, but the count is then one more than expected and nobody can say why.

The mechanism: `skip_header_lines` is a source-level parameter. Beam reads the first N lines of each file and discards them before emitting anything. It is applied *per file*, which matters: with a sharded input, every shard has its own header, and `skip_header_lines=1` removes one from each — which is what you want.

The alternative, and it is sometimes the right one, is to filter in a `Map` after parsing: `beam.Filter(lambda row: row["order_id"] != "order_id")`. This is more robust when you do not know whether every file has a header, or when the source is heterogeneous — one file with a header and one without. The cost is that the header row travels through your pipeline and through the shuffle if it is keyed before the filter, which is why the filter belongs as early as possible.

The production failure story: a pipeline read a CSV without skipping the header and wrote to BigQuery with `WRITE_APPEND`. The header row landed in the table as a record where `order_id` was the literal string `"order_id"`. Because BigQuery had inferred the column types from the data, the `amount` column was `FLOAT` and the header string was silently coerced to `NULL` — so the row was invisible in the table but present in the row count. A downstream `SUM(amount)` was correct by luck, but `COUNT(*)` was off by one per file, and the discrepancy grew every day.

Two other traps in the same area. A quoted CSV field containing a newline breaks a naive `line.split(",")` — the course's `try_parse_order_line` uses the `csv` module for exactly this reason. And a UTF-8 BOM at the start of the file makes the first column name `"\ufefforder_id"`, which then fails every lookup.

### 2. Why does `WriteToText` produce a sharded filename, and why must you never hard-code it?

Because the write is *distributed*. `WriteToText` writes to many files in parallel, so the output is `prefix00000of00003`, `prefix00001of00003`, `prefix00002of00003` — the shard index and the shard count. The default suffix template is `"-SSSSS-of-NNNNN"` with five digits each.

The consequence is that `WriteToText` is not a "write a file" operation; it is "write a directory of files". Any script that opens `out/summary` and expects to read it will fail with `FileNotFoundError`, and any script that globs `out/summary*` will pick up *every* shard, including shards from a previous run if the prefix was reused.

The mechanism: the number of shards is decided at run time from the parallelism the runner chose. With `num_shards=1` you get exactly one file, which is what `write_summary_to_csv` in the course's `transforms.py` does — but that means a single worker writes the whole output, which does not scale past a few hundred megabytes.

The production failure story: a nightly job wrote to `gs://bucket/summary`, and the downstream consumer read `gs://bucket/summary*`. One night a *backfill* ran into the same prefix and appended its shards alongside the nightly run's. The consumer globbed all of them and double-counted two days of revenue. The fix was to make the prefix unique per run — embed the partition date and the job ID in it — and to have the consumer read a manifest rather than a glob.

The rule that follows: **never hard-code an output filename, and make the output prefix unique per logical run.** If you need one file, use `num_shards=1` explicitly and understand that you have serialised the write.

### 3. Why does `WriteToText` call `str()` on whatever you give it, and what does that cost you?

Because `WriteToText` writes *text*. It takes each element, converts it with `str()`, and writes the result plus a newline. It does not serialise structures — it does not produce JSON, and it does not produce a CSV row.

The consequence is that `str()` on a dict produces Python's repr, not JSON:

```python
str({"region": "EMEA", "amount": 10.5})
# "{'region': 'EMEA', 'amount': 10.5}"
```

That is a valid Python literal but it is not valid JSON — single quotes, `True` instead of `true`, `None` instead of `null`. Any downstream consumer using `jq` or `json.loads` fails on it. The course's `format_summary_csv` exists precisely to avoid this: it uses `csv.writer` to build a proper CSV line, so a region name containing a comma gets quoted rather than corrupting the row.

The related trap: `str()` on a `float` is Python's repr, so `10.5` becomes `10.5` but `10.0` becomes `10.0` and a `Decimal` becomes `Decimal('10.5')` — which is not a number to any CSV reader. And `str(None)` is the four-character string `None`, which lands in your numeric column and fails the BigQuery load.

The production failure story: a pipeline wrote `WriteToText` output of dicts and a downstream job parsed it with `json.loads` per line. It worked for months because the dicts happened to contain only strings. When a field became an integer, the line became `{'order_id': 'o1', 'amount': 5}` — still not JSON — and the downstream job started failing with `JSONDecodeError: Expecting property name enclosed in double quotes`. The fix was to format explicitly, and the more robust fix was to stop writing text at all and write `beam.io.WriteToJson` or `WriteToBigQuery` directly.

### 4. What do the BigQuery write and create dispositions actually control, and which combination is safe?

Two independent flags. **`write_disposition`** controls what happens to the *rows* in the destination table: `WRITE_APPEND` adds them, `WRITE_EMPTY` requires the table to be empty (and fails otherwise), `WRITE_TRUNCATE` deletes the table's contents and then writes. **`create_disposition`** controls what happens to the *table*: `CREATE_IF_NEEDED` creates it if it does not exist, `CREATE_NEVER` requires it to already exist and fails otherwise.

The safe default is `WRITE_APPEND` + `CREATE_IF_NEEDED`. It is what the course's `batch_pipeline.py` uses, and it is idempotent-ish: re-running the job appends again rather than failing, and you can create the table by hand if you want full control over the schema.

The combination people reach for too eagerly is `WRITE_TRUNCATE` + `CREATE_IF_NEEDED`. It gives you "replace the table contents" semantics, which sounds exactly like what a nightly job wants — and it is, *only if* the job runs once and the table is not read while it runs. `WRITE_TRUNCATE` deletes the data first and writes afterwards, so there is a window where the table is empty. A dashboard querying during that window shows zero, and if the job then fails, the table stays empty. Worse, `WRITE_TRUNCATE` is not supported on all BigQuery destinations — it fails for some streaming and partitioned configurations.

The dangerous combination is `WRITE_APPEND` for a job that is supposed to be a *replace* — the nightly run appends to yesterday's data and the totals grow without bound.

The production failure story: a nightly job wrote with `WRITE_APPEND` to a table that was *also* written by a backfill. Because there was no partitioning and no deduplication, the revenue table contained the same orders twice, and nobody noticed for three weeks because the growth was gradual. The fix was to partition the table by ingestion date, write each run to its own partition, and use `WRITE_EMPTY` on that partition — a per-partition replace, which is atomic within the partition and safe to re-run.

### 5. What makes a sink idempotent, and why does it matter even when the source guarantees exactly-once?

An idempotent sink is one where writing the same element twice produces the same final state as writing it once. The property belongs to the *destination*, and no delivery guarantee upstream can substitute for it.

Three mechanisms make a BigQuery sink idempotent. First, **partition-keyed output**: write to a partition derived from the data (`_PARTITIONTIME` from the event date), and use `WRITE_EMPTY` on that partition — re-running the job replaces the partition rather than appending to it. Second, **a deterministic row identifier**: include a natural key in the row and deduplicate downstream with a `MERGE` or a `QUALIFY ROW_NUMBER() OVER (PARTITION BY key ORDER BY ts DESC)`. Third, **a deduplicating merge**: BigQuery `MERGE` on the key, so a re-run updates rather than inserts.

Note that the course's pipeline uses `WRITE_APPEND` and is therefore *not* idempotent — deliberately, because it is a batch job writing a fresh output table each run, and the output prefix is unique per run.

The reason the property matters even with an exactly-once source is the crash window. The runner's checkpoint and the sink's write are not one transaction. A worker can crash between "checkpoint committed" and "rows written", and the retry re-emits those rows. On Dataflow Streaming, checkpointing gives you effectively-once *processing*, but the sink write is outside that transaction.

The production failure story: a streaming job wrote click events to BigQuery with `WRITE_APPEND`. A worker was preempted mid-bundle; the bundle was retried; the events landed twice. Because the pipeline also computed a `COUNT(*)` per user per hour, the counts were inflated by a small, random percentage — about 0.3% — that nobody could attribute. The fix was to add a deterministic `event_id` and switch to a `MERGE` on it, so the retry updated rather than duplicated.

### 6. What are the parameters of `ReadFromPubSub` that matter, and what happens if you get them wrong?

The ones that matter are `topic`, `subscription`, `id_label`, and `timestamp_attribute`.

`id_label` is the deduplication mechanism. Pub/Sub delivers **at least once**, so the same message can be delivered more than once — after an ack deadline expires, a worker restart, or a redelivery policy. Setting `id_label` tells Beam to use the message's ID (or an attribute) to drop duplicates within the retention window. If you do not set it, every duplicate reaches your pipeline, and any stateful aggregation double-counts.

`timestamp_attribute` is how you get **event time** out of Pub/Sub. By default, Beam stamps every element with the *arrival* time, which means out-of-order messages land in the wrong window. Setting `timestamp_attribute` to an attribute your producer writes (an ISO-8601 timestamp, typically) moves the event time into the pipeline.

The two failure modes if you get these wrong are different. Wrong `id_label` (or none) produces *duplicate* results — a revenue dashboard that is 2% too high, with no error. Wrong `timestamp_attribute` (or none) produces *misplaced* results — the totals still sum correctly but the time series is wrong, which is worse because it looks right.

The mechanism for the deduplication: the source keeps a set of recently seen message IDs and suppresses repeats. The cost is memory proportional to the number of distinct IDs in the window, so `id_label` on a high-volume topic has a real memory cost on the worker.

The production failure story: a streaming pipeline read from Pub/Sub without `id_label`. The subscription had a 60-second ack deadline, and the pipeline's processing time regularly exceeded it under load, so messages were redelivered. Session counts inflated by 5–8%, and because the inflation varied with load, it looked like a genuine traffic pattern — the team spent a week investigating a phantom growth trend. The fix was `id_label="message_id"` plus raising the subscription's ack deadline to 300 seconds.

## Coders and schemas

### 7. How does Beam choose a coder, and what happens when it guesses wrong?

A coder is the serialisation format for a PCollection's elements. Beam picks one from the transform's type hints when they are available, and falls back to `FastPrimitivesCoder` with runtime inspection when they are not.

The rule of thumb: **add type hints and you get static coders and fast failures; omit them and you get runtime guessing and late failures.** A `Map` with an annotated function gets its coder chosen at pipeline construction. An unannotated `Map` gets `FastPrimitivesCoder`, which encodes a tuple or dict of primitives and can only *guess* the structure when it decodes.

The failure mode of guessing is specific and nasty. `FastPrimitivesCoder` encodes a `dict` as its *values* in insertion order, without the keys. On the write side that is fine. On the read side — a shuffle, a stateful operation, anything that persists and reloads — the keys come back from the coder's *schema*, and if the schema was guessed wrong the keys are wrong. The classic symptom is a `KeyError: 'region'` on a dict that demonstrably has the key, at a point in the pipeline where the data has been through a `GroupByKey` or a stateful `DoFn`.

The other failure is `TypeError: unhashable type: 'dict'` when a dict is used as a key. The coder is not at fault there — Beam requires hashable keys, so a dict key must become a tuple.

The production failure story: a pipeline read JSON events into dicts with an unannotated `Map`, then used `CombinePerKey` over a dict-valued accumulator. It ran correctly for a week, then a new event type arrived with a missing field, the accumulator's dict gained a new key, and the coder's encoding of the accumulator changed shape. The merge across workers then produced dicts whose key order differed between workers, and the final output had the columns transposed. The fix was to define an explicit typed accumulator — a named tuple or a fixed dict — and to add type hints so Beam used a stable coder.

### 8. What are `FastPrimitivesCoder`'s limits, and what should you use instead?

`FastPrimitivesCoder` encodes a tuple, or a dict of primitive values, and it is the default for good reason: it is fast and it does not require a schema. Its limits are real, though.

It handles **primitives only**: `int`, `float`, `bool`, `str`, `bytes`, `None`, and nested tuples/dicts of those. It does **not** handle arbitrary Python objects, `datetime`, `Decimal`, `set`, or a custom class — for those it needs a registered coder, and if there is none you get a `TypeError` at run time, on a worker, when the element is first encoded.

Its second limit is the dict-key problem described above: a dict is encoded as its values plus a separate schema, and the schema must be inferable. A dict whose keys differ across elements is a problem — the coder's schema is fixed per PCollection, so heterogeneous dicts either fail or produce missing keys.

Its third limit is performance on large nested structures: it is a reflective, Python-level encoder, so a deeply nested structure is slow to serialise, and that cost is paid on every shuffle.

The alternatives. `TupleCoder` for heterogeneous tuples with a known shape. `AvroCoder` for a fixed schema with named fields — the right choice when the schema is a contract. `RowCoder` for `apache_beam.Row`, which is the interoperable row type for BigQuery and for tabular formats, and gives you named fields without an Avro schema. `StrUtf8Coder` for plain strings. And a **custom coder** when you have a domain type — a `dataclass` or a `NamedTuple` — and want it to survive the shuffle intact.

The production failure story: a pipeline used `datetime` objects inside a dict accumulator. `FastPrimitivesCoder` cannot encode them, and the job failed on the first worker with `TypeError: Cannot encode datetime.datetime as a FastPrimitivesCoder value` — 15 minutes after submission, having already provisioned and billed for the workers. The fix was to convert to a Unix timestamp float at the boundary (which is what the course's `parse_timestamp` returns as a `datetime` but the pipeline converts with `Timestamp(float(...))`) and to use `AvroCoder` or `RowCoder` where a schema was warranted.

### 9. What is `apache_beam.Row`, when should you use it, and what is it not?

`apache_beam.Row` is Beam's interoperable row type — a schema'd, positional row with named fields. It is the Python equivalent of a table row, and it is what `RowCoder` encodes.

Use it when you are producing tabular output: BigQuery, Avro, Parquet, CSV. It gives you named fields, so the schema travels with the data, and it interoperates with the schema-aware readers and writers.

It is **not** a general-purpose record type, and this is the boundary people cross. A `Row` is positional: its fields are indexed, and the *schema* — the list of field names — is separate and external. `Row` does not carry its own schema with it through a shuffle in a self-describing way; the coder is what preserves the names, and the schema must be consistent across the PCollection.

It is also not a replacement for a typed domain object. If you have a `Order` dataclass with validation and methods, keep it as a dataclass in the pure-logic layer, and convert to `Row` at the sink boundary. That is exactly the split the course's `transforms.py` makes: a pure half that does not need Beam, and a Beam half that adapts to it.

The production failure story: a team used `Row` for an intermediate stage and then added a field to the schema in one branch of the pipeline but not another. `RowCoder` enforces the schema it was given, so the branches produced incompatible rows, and the `Flatten` between them failed at run time with a schema mismatch. The fix was to normalise to a single schema at the branch point rather than hoping the rows would reconcile.

### 10. When do you reach for Avro, Parquet, or CSV, and what is the actual trade-off?

**CSV** is for humans and for legacy systems. It is the most portable format in existence and the worst for analytics: no types, no nesting, ambiguous quoting, and no parallelism-friendly compression. Use it at the edges — an export, a hand-off to a partner — and parse it into typed records immediately.

**Avro** is for *schema-on-read* contracts. It carries its schema in the file header, supports nested and evolving schemas with a well-defined compatibility model, and is the native interchange format of the Kafka ecosystem. It is the right choice when the producer and consumer are different teams and the schema is a contract that evolves.

**Parquet** is for *columnar analytics*. It is columnar, so a query that reads three columns out of forty reads three columns' worth of bytes; it compresses well (typically 5–10× on typical data); and it supports predicate pushdown, so filters skip row groups before reading them. It is the right choice when the output is going to be read by a query engine — BigQuery external tables, Spark, DuckDB, Athena.

The decision rule: **CSV at the boundary with humans, Parquet at the boundary with query engines, Avro at the boundary with other stream processors.** And note that all three are supported by Beam's I/O: `ReadFromAvro`/`WriteToAvro`, `ReadFromParquet`/`WriteToParquet`, `ReadFromCsv`/`ReadFromText` with a parser.

The production failure story: a team stored 2 TB of order data as CSV in GCS and queried it with BigQuery external tables. Every query scanned the whole 2 TB because there are no column statistics to prune on and no predicate pushdown. Moving to Parquet cut the query cost by roughly 8× and the storage by 6×, and — more importantly — the nightly aggregate job went from 40 minutes to 6, because it was reading three columns rather than forty.

## File formats and multi-source

### 11. What is the schema-evolution trap in a batch pipeline, and how do you avoid it?

The trap is that a batch pipeline's "schema" is usually implicit — inferred from the data, or defined by the code that reads it — and the two drift apart the moment the upstream changes. BigQuery's `infer_schema` makes it worse: the table schema is fixed at creation time from the first batch, and later batches are coerced into it. A new column in the CSV is *dropped*, not added.

The failure is silent and it is expensive. The upstream added a `discount_code` field. BigQuery's schema did not have it, so the values were discarded without error. Two months later someone needed that column, backfilled from source, and discovered the current table had no discount data at all — the field had been silently dropped for the whole period.

The way to avoid it is to **stop inferring**. Create the table explicitly with `CREATE_IF_NEEDED` and a schema you define, and write with `ignore_unknown_columns=False` so a new upstream column causes a *loud* failure rather than a silent drop. When you *want* to absorb a new column, add it to the schema deliberately, and use `ignore_unknown_columns=True` only for the transition.

The batch-specific part is that a batch job can be re-run over historical data, which means schema change is a *time-travel* problem: today's schema applied to six months of data may not fit. The approaches are to version the schema and pick the right one per partition date, to normalise to a canonical schema early with defaults for missing fields, or to keep the raw payload and transform it later.

The production failure story: a nightly job wrote to a BigQuery table created with `CREATE_IF_NEEDED` and no explicit schema. The upstream added a `channel` column in month three. The nightly job kept succeeding, the table kept its original nine columns, and a business report that needed `channel` was silently wrong — it reported every order as having the default channel. The fix was an explicit schema with `ignore_unknown_columns=False`, plus a schema-change runbook that requires a deliberate table migration.

### 12. How do you read from multiple sources in one pipeline, and what is the tag pattern for?

`Flatten` merges PCollections from different sources into one. Read each source into its own PCollection, then flatten. The tag pattern is the variant where you need to know *which* source each element came from: tag each branch before flattening, and split the flattened result back out by tag.

```python
import apache_beam as beam

with beam.Pipeline() as p:
    orders = p | "ReadOrders" >> beam.io.ReadFromText("gs://bucket/orders.csv")
    refunds = p | "ReadRefunds" >> beam.io.ReadFromText("gs://bucket/refunds.csv")
    combined = ({"orders": orders, "refunds": refunds} | "Flatten" >> beam.Flatten())
    _ = combined | "Print" >> beam.Map(print)
```

The tag pattern, when the source matters downstream, is to attach the source name to each element *before* flattening:

```python
import apache_beam as beam

with beam.Pipeline() as p:
    orders = p | "ReadOrders" >> beam.io.ReadFromText("gs://bucket/orders.csv")
    refunds = p | "ReadRefunds" >> beam.io.ReadFromText("gs://bucket/refunds.csv")
    tagged = (
        {
            "orders": orders | "TagOrders" >> beam.Map(lambda row: ("orders", row)),
            "refunds": refunds | "TagRefunds" >> beam.Map(lambda row: ("refunds", row)),
        }
        | "Flatten" >> beam.Flatten()
    )
    _ = tagged | "Print" >> beam.Map(print)
```

Each element after the flatten is a `(source_name, row)` tuple, so the downstream can branch on the source without a second pass. The cost is one extra field per element and one extra `Map` per branch; the benefit is that source-specific logic (different validation rules, different downstream sinks) becomes a simple `Filter` on the tag rather than a separate branch from the source.

The important constraint is **coder compatibility** across the flattened branches. Both branches must produce elements with the same coder. If one branch yields `str` and the other yields `dict`, the flatten either fails at run time or produces elements that are structurally different.

The alternative to `Flatten` is to keep the sources separate and join them with `CoGroupByKey` — which is the right move when the sources need to be *combined* rather than *concatenated*. A concatenation is for "more rows of the same kind"; a join is for "rows that relate to each other".

The production failure story: a pipeline flattened two CSV sources — orders with 9 fields and refunds with 11 — because both were parsed into dicts. The two dicts had different key sets, and `FastPrimitivesCoder` encoded them with a single schema, so every refund row's `amount` landed in the `reason` column. No exception was raised; the output was 200,000 rows of subtly wrong data. The fix was to normalise both branches to the same explicit schema — using `Row` with `RowCoder`, or an explicit dict construction — before flattening.

### 13. What is the shard-explosion problem, and how do you prevent it?

Shard explosion is the situation where a pipeline writes an enormous number of tiny output files — one per bundle, or one per worker, or one per key — which then makes the *downstream* read slow and expensive. Cloud Storage charges per object and per list operation, so millions of 1 KB objects cost real money and take real time to enumerate.

The usual causes. A `WriteToText` with the default `num_shards=0` (auto) on a small input: the runner may still choose many shards, and each shard is a separate object. A `WriteToBigQuery` with a very small `max_file_size` or an aggressive `max_files_per_bundle`. And the worst one: writing one file *per key* with a `WriteToText` inside a per-element transform — that is one object per key, and a pipeline keyed by `customer_id` can easily produce millions.

The prevention is explicit and mostly about choosing shard counts deliberately rather than letting them default. Set `num_shards` to a number you chose, sized to your output: for a 10 GB output, 64–256 shards of 40–160 MB each is a reasonable target. Keep BigQuery's `max_file_size` in the tens-of-megabytes range. And never write a file per element — write per *bundle*, or per partition.

There is a hard constraint worth knowing: `num_shards` must be at least 1, and if you set it explicitly, the runner honours it. Setting `num_shards=1` on a 10 GB output serialises the write onto one worker — a real trade-off, and the reason the course's `write_summary_to_csv` uses `num_shards=1` only because its output is a handful of summary rows.

The production failure story: a pipeline wrote a per-partition export with `num_shards` unset, and the Dataflow autoscaler spun up 200 workers for a 5-minute job. The output was 8,000 files averaging 60 KB each. The downstream consumer, a BigQuery external table over the prefix, took 40 minutes to load what was 480 MB of data — the load time was entirely object-listing overhead. The fix was `num_shards=8` for that job, which brought the load time to 90 seconds.

### 14. What are `ReadFromPubSub`'s limits, and when should BigQuery be a source instead?

`ReadFromPubSub` is the only realistic way to get a genuinely unbounded, continuously-arriving stream into Beam, and it is the right tool for event data with a natural publish time. Its cost is real, though: **at-least-once delivery, a per-message ack, and a per-message cost**, plus the per-GB charge Dataflow bills for streaming data processed. Every message you read is billed, even if you then discard it.

BigQuery as a source is the other option, and it is usually the better one for *backfills* and for *reprocessing historical data*. Reading a BigQuery table through `beam.io.ReadFromBigQuery` gives you a bounded, snapshot-consistent input, and you can process 10 TB of history in a batch job for a fraction of the cost of streaming it through Pub/Sub.

The decision rule: **Pub/Sub for live arrival, BigQuery for history.** If you need both — a backfill plus a live tail — the common pattern is to run the same Beam pipeline twice: once with a BigQuery source over the historical partition, once with a Pub/Sub source for the live tail, with the outputs written to disjoint partitions so the two runs compose.

The trap in reading BigQuery is cost. `ReadFromBigQuery` issues a query and reads the results through the BigQuery Storage API, and you are billed for the query's bytes scanned *and* for the Dataflow workers that read the results. A pipeline that reads a whole table and filters 2% of it in Beam is far more expensive than the same filter expressed in the BigQuery query itself. Push the filter down.

The production failure story: a team built a "streaming" pipeline that read the entire orders table from BigQuery every hour, filtered to the last hour's rows in Beam, and aggregated. Each run scanned 8 TB and cost roughly $40 in BigQuery query fees alone, to produce an hourly number for 4 GB of relevant data. The fix was to add the timestamp predicate to the BigQuery query so the scan was 4 GB, and the run cost dropped to cents. The same shape of bug is the reason a `ReadFromPubSub` pipeline that reads a topic and then throws away 98% of the messages is usually a design smell — you are paying per byte to discard it.
