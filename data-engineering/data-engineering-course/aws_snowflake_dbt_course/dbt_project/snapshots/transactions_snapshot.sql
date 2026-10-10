-- ============================================================================
-- snapshots/transactions_snapshot.sql
-- ----------------------------------------------------------------------------
-- Snapshot of the transactions mart using the timestamp strategy.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
--
-- Lecture reference: L121 "Snapshots: The Timestamp Strategy",
-- L122 "Snapshot Configurations", L123 "Snapshots: The Check Strategy".
--
-- dbt snapshots capture slowly-changing dimensions (SCD Type 2) — every
-- run, dbt checks the source table for changed rows (by `updated_at` or
-- by checking a list of columns) and inserts a new "version" when a row
-- has changed.
-- ============================================================================

{% snapshot transactions_snapshot %}

{{
    config(
      target_database='DBT_SNOWFLAKE_DBT',
      target_schema='snapshots',
      strategy='timestamp',
      unique_key='tx_hash',
      updated_at='block_timestamp',
      invalidate_hard_deletes=True,
    )
}}

select * from {{ ref('transactions') }}

{% endsnapshot %}
