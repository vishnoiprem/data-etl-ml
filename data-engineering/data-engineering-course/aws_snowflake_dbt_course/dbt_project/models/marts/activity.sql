-- ============================================================================
-- models/marts/activity.sql
-- ----------------------------------------------------------------------------
-- Mart model: daily Ethereum activity by category.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
--
-- Lecture reference: L19 "Daily Ethereum Activity by Category".
--
-- Incremental model demonstrating the merge strategy + is_incremental()
-- guard. Materialization precedence: the in-model config block below
-- (incremental merge) overrides the project-wide 'table' default from
-- dbt_project.yml and the folder-level 'table' default.
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
          tx_date                                          as activity_date
        , tx_category
        , count(*)                                          as tx_count
        , sum(value_eth)                                    as total_value_eth
        , avg(tx_fee_eth)                                   as avg_tx_fee_eth
    from transactions
    group by 1, 2

)

select * from aggregated
