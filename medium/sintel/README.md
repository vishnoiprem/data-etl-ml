# RepoSphere: Idempotent Micro-Batch Event Merge with Schema Drift

You are a senior data engineer at **RepoSphere**, a large-scale SCM platform. RepoSphere ingestion has shifted from once-a-day dumps to **micro-batches** dropped onto S3 throughout the day. Your job is to merge each batch into a curated event table that downstream dashboards trust.

The pipeline must survive everything that real ingestion throws at it:

- Duplicate / corrected events: the same `event_id` can arrive in multiple batches with different payloads. The version with the highest `ingested_at` wins; older versions must be **archived**, not silently lost.
- Schema drift: new event types (`release`, `fork`, …) bring new top-level fields. The curated table's schema must **auto-evolve** (union of fields), but rows missing required core fields (`event_id`, `repo.id`, `created_at`) must be redirected to a **quarantine** path with a reason.
- Late arrivals: events whose `created_at` is more than **7 days** before the job's run date must land in a separate **late_arrivals** output, not in curated.
- Idempotency: the job takes a `run_date` and must be **safely re-runnable**. Re-running the same batch with the same `run_date` must not double-count or change the curated table content.
- Observability: a `_metrics` row must report rows quarantined, rows late, rows inserted, rows updated, and the list of new fields seen on this run.

## Environment

- Python version: 3.12
- PySpark Version: 3.5.5

## Read-Only Files

- `src/app.py`
- `src/tests/*`
- `src/main/base/*`
- `data/*`

## Commands

- install:
```bash
virtualenv venv && source venv/bin/activate && pip3 install -r requirements.txt
```
- test:
```bash
virtualenv venv && source venv/bin/activate && pip3 install -r requirements.txt && py.test -p no:warnings --junitxml=unit.xml
```
- run:
```bash
virtualenv venv && source venv/bin/activate && pip3 install -r requirements.txt && python3 src/app.py data/batch_2026_05_01.jsonl 2026-05-01
```

## Requirements

This project includes the following:

**Data Files**

Sample file is provided in _data/_:

- _batch_2026_05_01.jsonl_
  - JSON Lines (1 JSON per line)
  - Each event has keys: _event_id_, _event_type_, _created_at_, _ingested_at_, _repo_ (`{id, name}`), _actor_ (`{id, login}`), plus zero or more optional top-level fields (`branch`, `release_tag`, `fork_parent_id`, …) which appear as new event types are introduced.

**Functionality**

The project is partially completed. You must implement the following methods in the class _PySparkJob_ (in _src/main/job/pipeline.py_) so that the unit tests pass.

**Method requirements**

- _read_events_batch(self, input_path: str) -> DataFrame_
  - Read JSON lines and return a DataFrame of nested events.
  - Must not assume every optional top-level field exists in the batch.

- _read_curated_if_exists(self, curated_path: str) -> DataFrame_
  - "Exists" means: the path exists as a directory on the local filesystem AND that directory contains at least one file. In that case, read the directory as Parquet and return the DataFrame (you may assume the contents are a valid Parquet table).
  - Otherwise (path missing, not a directory, or directory present but containing no files), return an **empty** DataFrame whose schema includes at least these core columns: _event_id_ (string), _event_type_ (string), _created_ts_ (timestamp), _ingested_ts_ (timestamp), _repo_id_ (string), _repo_name_ (string), _actor_login_ (string).
  - You do NOT have to handle the case where the directory exists with files but the contents are not Parquet, nor the case where Parquet files exist but contain zero rows — neither will be tested.

- _quarantine_events(self, events_df: DataFrame) -> DataFrame_

  Returns ONLY the rows that must be quarantined, with an added _quarantine_reason_ column. A row is quarantined if any of the following holds (check in this order — first match wins):

  1. _event_id_ is NULL or empty → reason `"missing_event_id"`.
  2. _repo.id_ is NULL → reason `"missing_repo_id"`.
  3. _created_at_ is NULL or cannot be parsed as a timestamp → reason `"invalid_created_at"`.

  Well-formed rows must NOT appear in the output.

- _extract_late_arrivals(self, events_df: DataFrame, run_date: str) -> DataFrame_

  Returns ONLY the rows that are well-formed (i.e. would pass the quarantine checks) AND whose _created_at_ is strictly more than 7 days before _run_date_ (where _run_date_ is interpreted as midnight UTC). The output must be **flattened** (same columns as the curated schema below, plus any extra top-level fields from the input).

- _extract_fresh_events(self, events_df: DataFrame, run_date: str) -> DataFrame_

  Returns ONLY the rows that are well-formed AND not late (i.e. _created_at_ ≥ run_date midnight UTC − 7 days). The output must be **flattened** the same way:

  Core curated columns:
  - _event_id_ (string), _event_type_ (string)
  - _created_ts_ (timestamp): parsed from _created_at_
  - _ingested_ts_ (timestamp): parsed from _ingested_at_
  - _repo_id_ (string): from `repo.id`
  - _repo_name_ (string): from `repo.name`
  - _actor_login_ (string): from `actor.login`

  Plus any optional top-level scalar fields present in the input batch (e.g. `branch`, `release_tag`, `fork_parent_id`) carried through verbatim — this is how schema drift propagates.

- _merge_into_curated(self, curated_df: DataFrame, fresh_events_df: DataFrame) -> DataFrame_

  Performs an **idempotent upsert** merge.

  - The output schema must be the **union** of the two input schemas. Columns present in one side but not the other must appear in the output, with NULL values for rows that didn't have that column.
  - For each _event_id_, the output must contain exactly **one** row: the row with the highest _ingested_ts_ across both sides. Ties (same _event_id_ and same _ingested_ts_ on both sides) are not data-quality concerns — the content is assumed identical; keep either.
  - The merge must be order-independent: merging batch A then batch B must produce the same curated table as merging B then A, given the same starting curated state. Reruns of the same batch against its own output must therefore be a no-op (the **idempotency** property).

- _extract_archived_versions(self, curated_df: DataFrame, fresh_events_df: DataFrame) -> DataFrame_

  Returns the rows from _curated_df_ that are **superseded** by this batch — i.e. an _event_id_ that exists in _curated_df_ and also appears in _fresh_events_df_ with a **strictly newer** _ingested_ts_.

  - These are the OLD versions (the ones being replaced), preserved in case we need to inspect history.
  - Same _event_id_ with equal _ingested_ts_ in both sides is NOT a supersession (so idempotent reruns produce an empty archive).
  - Output schema = same columns as _curated_df_.

- _compute_drift_metrics(self, curated_before, curated_after, quarantine_df, late_arrivals_df, fresh_events_df, run_date: str) -> DataFrame_

  Produces a **single-row** DataFrame with these columns (in any order):

  - _run_date_ (date): parsed from the _run_date_ string.
  - _rows_quarantined_ (int): count of _quarantine_df_.
  - _rows_late_ (int): count of _late_arrivals_df_.
  - _rows_inserted_ (int): number of distinct _event_id_s in _fresh_events_df_ that were NOT present in _curated_before_.
  - _rows_updated_ (int): number of distinct _event_id_s present in _curated_before_ whose maximum _ingested_ts_ in _fresh_events_df_ is **strictly newer** than the existing _ingested_ts_ in _curated_before_ (i.e. the row was actually superseded). On an idempotent rerun this must be 0.
  - _new_fields_added_ (array<string>): the sorted list of column names that are in _curated_after_ but were NOT in _curated_before_.

Complete the implementation so that the unit tests pass. You can use the given tests to check your progress while solving the problem.

<details><summary>Job in Action</summary>

```python
def main():
    job = PySparkJob()

    events_df = job.read_events_batch("data/batch_2026_05_01.jsonl")
    curated_before = job.read_curated_if_exists("/some/curated/path")

    quarantine_df = job.quarantine_events(events_df)
    late_df = job.extract_late_arrivals(events_df, "2026-05-01")
    fresh_df = job.extract_fresh_events(events_df, "2026-05-01")

    curated_after = job.merge_into_curated(curated_before, fresh_df)
    archived_df = job.extract_archived_versions(curated_before, fresh_df)

    metrics_df = job.compute_drift_metrics(
        curated_before, curated_after, quarantine_df, late_df, fresh_df, "2026-05-01"
    )
    metrics_df.show(truncate=False)
```

</details>