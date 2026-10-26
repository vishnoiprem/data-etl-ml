-- ============================================================================
-- 03_section / code / activity_incremental.sql
-- ----------------------------------------------------------------------------
-- Stand-alone dbt incremental model for the activity mart.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

{{ config(
    materialized='incremental',
    unique_key='activity_date',
    on_schema_change='append_new_columns',
    incremental_strategy='merge'
) }}

with transactions as (

    select * from {{ ref('transactions') }}
    {% if is_incremental() %}
      where block_timestamp >= (select dateadd('day', -3, max(activity_date)) from {{ this }})
    {% endif %}

),

aggregated as (

    select
          block_timestamp::date             as activity_date
        , count(*)                          as tx_count
        , sum(value_eth)                    as total_value_eth
    from transactions
    group by 1

)

select * from aggregated
