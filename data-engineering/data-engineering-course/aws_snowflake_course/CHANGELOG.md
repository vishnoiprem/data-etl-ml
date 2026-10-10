# CHANGELOG — Snowflake — The Complete Masterclass

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

All notable changes to this course are recorded here.

## [1.0.0] — 2026-10-10

### Added
- **192 lecture scripts** across **28 sections** (Welcome! → Bonus), 1:1
  with the published course syllabus.
- **28 section quizzes** (8–12 questions each, hidden-answer pattern).
- **15 working SQL demos** that are idempotent and runnable against the
  Snowflake free trial:
  - `04_warehouses/code/setup_warehouse.sql`
  - `07_json_parquet/code/load_csv.sql` (with `parse_json.sql`,
    `flatten_array.sql`)
  - `08_parquet_performance/code/copy_options.sql`
  - `12_unload_snowpipe/code/aws_storage_integration.sql`
  - `15_snowpipe_advanced/code/unload_snowpipe.sql`
  - `16_time_travel/code/cortex_ai_demo.sql`
  - `19_data_sharing/code/time_travel_demo.sql` (+ `undrop.sql`)
  - `22_streams/code/clone_database.sql`
  - `23_materialized_views/code/create_share.sql` (+ reader account)
  - `25_roles_deep_dive/code/create_task.sql`
  - `26_bi_tools/code/create_stream.sql`
  - `27_best_practices/code/create_materialized_view.sql`
  - `28_bonus/code/masking_policy.sql`, `rbac_grants.sql`
- **4 Python test suites** (53 tests) using `snowflake-connector-python`
  + `pytest-mock` so they pass without a live Snowflake account.
- **6 mermaid diagrams** in `diagrams/`:
  - `snowflake_architecture.mmd`
  - `warehouse_scaling.mmd`
  - `storage_integration_flow.mmd`
  - `snowpipe_architecture.mmd`
  - `cortex_ai_stack.mmd`
  - `data_sharing_topology.mmd`
- **4 hands-on assignments** in `assignments/`:
  - `assignment_1_end_to_end_etl.md`
  - `assignment_2_cortex_ai_app.md`
  - `assignment_3_cdc_pipeline.md`
  - `assignment_4_secure_data_share.md`
- **3 PDF slide placeholders** in `downloads/`.

### Notes
- All SQL files use `IF NOT EXISTS` / `OR REPLACE` so they're idempotent
  and safe to re-run.
- Python tests mock the Snowflake connector so the suite passes
  in CI without secrets.
- Not affiliated with Snowflake Inc. (the published course is similarly
  disclaimed).

---

**Prem Vishnoi** — pvishnoi@avilx.com
