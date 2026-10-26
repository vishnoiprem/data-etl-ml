# Assignment 1 — Ethereum ETL Pipeline

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Estimated time:** 4-6 hours
> **Sections tested:** 1, 2, 3, 5, 6

## Goal

Build a complete end-to-end dbt project that loads Ethereum
transactions from a public S3 feed into Snowflake, transforms them
through staging + marts, and exposes 3 mart tables with passing
tests.

## Steps

1. **Set up Snowflake** (Section 1, L06-L08):
   - Create a free trial account
   - Create a database `DBT_SNOWFLAKE_DBT_DEV`
   - Create a warehouse `TRANSFORMING`
   - Create a stage pointing to `s3://aws-public-blockchain/v1.0/eth/transactions/`

2. **Load raw data** (Section 1, L08):
   - Use `COPY INTO` to load 100,000 transactions into `RAW.ETHEREUM.raw_transactions`
   - Same for `raw_blocks`

3. **Configure dbt** (Section 1, L13-L14):
   - `dbt init dbt_ethereum`
   - Set up key pair authentication
   - Edit `profiles.yml` with your account, user, db, schema

4. **Build staging** (Section 3, L21-L22):
   - Add `models/staging/_sources.yml` with the 2 raw tables
   - Add `models/staging/stg_ethereum__transactions.sql` (renaming + casting)
   - Add `models/staging/stg_ethereum__blocks.sql`

5. **Build marts** (Section 2, L17-L20 + Section 3, L25):
   - `models/marts/transactions.sql` (incremental merge)
   - `models/marts/activity.sql` (incremental merge)
   - `models/marts/stablecoin_activity.sql`

6. **Add tests** (Section 6, L42):
   - not_null + unique on `tx_hash`
   - accepted_values on `tx_category`
   - 1 custom generic test (positive_value on `value_eth`)

## Acceptance criteria

- [ ] `dbt run` succeeds (all models built)
- [ ] `dbt test` passes (all tests green)
- [ ] `dbt run --select transactions+` rebuilds the dependent chain
- [ ] Re-running `dbt run` is a no-op for incremental models
- [ ] The 3 mart tables exist in `DBT_SNOWFLAKE_DBT_DEV.PUBLIC_MARTS`

## Submission

Save your `dbt_project/` as `assignment_1_submission/` and include
`run_results.json` + a screenshot of `dbt test` output.
