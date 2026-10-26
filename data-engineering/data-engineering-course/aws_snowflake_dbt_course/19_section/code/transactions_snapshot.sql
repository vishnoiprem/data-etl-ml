-- ============================================================================
-- 19_section / code / transactions_snapshot.sql
-- ----------------------------------------------------------------------------
-- Stand-alone snapshot demo using the timestamp strategy.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

{% snapshot transactions_demo_snapshot %}

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

select
      tx_hash
    , block_timestamp
    , from_address
    , to_address
    , value_eth
    , tx_category
from {{ ref('transactions') }}

{% endsnapshot %}
