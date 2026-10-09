# Module 03 — Extraction

> **6 lessons · ~3 hours**

The first "E" in ETL. This module is the workhorse of the track:
full vs incremental extraction, Change Data Capture, API polling,
JDBC connectors, schema evolution, and backpressure. By the end
you'll be able to talk about extraction for an hour without
repeating yourself.

Author: **Prem Vishnoi &lt;prem.vishnoi@example.com&gt;**

---

## Lessons

| # | Lesson | What you'll learn |
|---|---|---|
| 08 | [Extraction Patterns: Full vs Incremental](design/08_extraction_patterns_full_vs_incremental.md) | When to reload the world, when to diff. |
| 09 | [CDC (Change Data Capture)](design/09_cdc_change_data_capture.md) | Debezium-style CDC: log-based, low-latency, complete. |
| 10 | [API Polling and Webhook Ingestion](design/10_api_polling_and_webhook_ingestion.md) | Cursor pagination, rate limits, webhooks. |
| 11 | [JDBC/ODBC Connectors and SQL Sources](design/11_jdbc_odbc_connectors_and_sql_sources.md) | Polling SQL sources, watermarking, slot management. |
| 12 | [Schema Evolution and Backward Compatibility](design/12_schema_evolution_and_backward_compatibility.md) | Schema registry, contract tests, breaking changes. |
| 13 | [Extraction at Scale: Backpressure, Batching, Parallelism](design/13_extraction_at_scale.md) | When the source out-produces the pipeline. |

---

## Code

- [`code/cdc.py`](code/cdc.py) — Debezium-style CDC pipeline
  (snapshot + diff → INSERT/UPDATE/DELETE events).
- [`code/api_poller.py`](code/api_poller.py) — paginated HTTP
  extractor with rate-limit handling.
- [`code/jdbc_extractor.py`](code/jdbc_extractor.py) — incremental
  SQL extractor with `updated_at` watermark.
- [`code/schema_registry.py`](code/schema_registry.py) — schema
  evolution tracker and contract checker.
- [`tests/test_extraction.py`](tests/test_extraction.py) — 25 unit
  tests covering all four modules.

---

## How the code connects to the lessons

Every design lesson in this module maps to a class in `code/`:

| Lesson | Code |
|---|---|
| 08 (full vs incremental) | `jdbc_extractor.IncrementalExtractor` |
| 09 (CDC) | `cdc.CDCPipeline` |
| 10 (API polling) | `api_poller.ApiPoller` |
| 11 (JDBC) | `jdbc_extractor.JDBCExtractor` |
| 12 (schema evolution) | `schema_registry.SchemaRegistry` |
| 13 (backpressure) | `cdc.CDCPipeline` (re-uses batching internally) |

Read the lesson, then read the code, then run the test. The pattern
is the same in every module of this track.
