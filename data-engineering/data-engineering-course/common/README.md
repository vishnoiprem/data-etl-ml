# `common/` — Data Engineering Shared Library

A small, dependency-free Python library shared by the new data
engineering tracks (`data_modeling/`, `data_pipeline_design/`,
`sql_interviews/`, `coding_interviews/`). It mirrors the role of
`system_design/common/` — keep the cross-cutting helpers in one
place so every exercise reads the same way.

Author: **Prem Vishnoi &lt;pvishnoi@avilx.com&gt;**

## Modules

| Module | Purpose |
| --- | --- |
| `schema.py` | `Column`, `Table` dataclasses plus `create_table_sqlite`, `create_index_sqlite`, `drop_table_sqlite`, `add_foreign_keys`. Generates DDL for `CREATE TABLE IF NOT EXISTS`. |
| `query.py` | `QueryRunner` — a tiny SQLite wrapper with `execute`, `executemany`, `query_all`, `query_one`, `query_iter`. Works as a context manager. |
| `data_gen.py` | Deterministic synthetic generators: `make_users`, `make_products`, `make_orders`, `make_events`. All seedable; all return `list[dict]` with snake_case keys and ISO 8601 timestamps. |
| `pipeline.py` | `Pipeline(name, extract, transform, load, retries=3)` with per-stage retries, optional idempotency key, and a `state` dict for offsets. `with_idempotency(key, fn)` caches results in a local SQLite. |
| `fixtures.py` | `SAMPLE_DATA_DIR`, `fixture_path(name)`, `list_fixtures(suffix=...)`. |
| `csv_utils.py` | `read_csv`, `write_csv`, `stream_csv`, plus `read_jsonl` / `write_jsonl`. Pure stdlib. |
| `analytics.py` | `running_total`, `rank_desc` (with ties), `dedupe_by_key`, `p50_p95_p99`, `top_k_by`, `group_count`, `safe_div`. |
| `jinja_helpers.py` | `render_sql(template, **vars)` — tiny `{{ var }}` and `{% if var %}` substitution with safe SQL value coercion. No external deps. |
| `conftest_helpers.py` | Factories tracks can wrap in `@pytest.fixture`: `make_tmp_db`, `build_seeded_runner`. |

## Quick start

```python
from common import QueryRunner, Table, Column, make_orders

# Define a schema
users = Table("users", [
    Column("id", "INTEGER", primary_key=True),
    Column("email", "TEXT", nullable=False),
])

# Talk to SQLite
q = QueryRunner(":memory:")
q.execute(users.to_ddl())
q.executemany(
    "INSERT INTO users(id, email) VALUES (?, ?)",
    [(i, f"u{i}@x.com") for i in range(1, 4)],
)
print(q.query_all("SELECT email FROM users ORDER BY id"))
q.close()
```

## Sample data

The `sample_data/` directory at the course root holds deterministic
CSV / JSONL fixtures for the tracks to share. Use the helpers in
`common.fixtures` to find them:

```python
from common.fixtures import SAMPLE_DATA_DIR, fixture_path

SAMPLE_DATA_DIR          # -> Path(".../sample_data")
fixture_path("users.csv")  # -> Path(".../sample_data/users.csv")
```

To regenerate the fixtures: `python3 sample_data/generate.py`.

## Running the test suite

```bash
python3 scripts/run_all_tests.py            # all tracks
python3 scripts/run_all_tests.py common     # one track
python3 scripts/run_all_tests.py -v         # verbose
```

The script discovers every `<track>/tests/test_*.py` file, runs it
with `unittest.TextTestRunner`, and prints a per-track summary.
Exit code is `0` only if every track passes.
