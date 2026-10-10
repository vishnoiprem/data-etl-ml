# Assignment 2 — Incremental Strategy Comparison

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Estimated time:** 2-3 hours
> **Sections tested:** 3, 6, 7

## Goal

Compare the three incremental strategies (append, merge, delete+insert)
on the same model and document the trade-offs.

## Steps

1. **Build 3 versions of the same model** in `dbt_project/`:
   - `models/marts/activity_append.sql` (incremental_strategy='append')
   - `models/marts/activity_merge.sql` (incremental_strategy='merge')
   - `models/marts/activity_delete_insert.sql` (delete+insert)

2. **Run each version 5 times** with a fresh source table of 100,000 rows.

3. **Measure**:
   - Time to run (dbt run --select <version>)
   - Rows in target table after each run
   - Cost (compute credits in Snowflake)

4. **Document** in a `comparison.md` file:
   - When is each strategy appropriate?
   - What's the unique_key behavior for each?
   - Which would you use for the transactions mart? Why?

## Bonus

Add a `cluster_by` config to one of the variants and measure the
query performance impact on a downstream analytical query.

## Acceptance criteria

- [ ] 3 model files exist
- [ ] Each model has been run 5 times (15 total `dbt run` invocations)
- [ ] `comparison.md` is filled in with timing data
