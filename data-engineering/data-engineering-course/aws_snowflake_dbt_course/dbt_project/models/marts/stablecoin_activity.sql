-- ============================================================================
-- models/marts/stablecoin_activity.sql
-- ----------------------------------------------------------------------------
-- Mart model: daily stablecoin (USDT/USDC) transfer activity.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
--
-- Lecture reference: L20 "Daily Stablecoin Activity (USDT & USDC)".
-- Demonstrates:
--   - Joining two staging models
--   - Filtering by a list-shaped variable (var('stablecoin_addresses'))
--   - Performance via clustering key on the date column
-- ============================================================================

{{ config(
    materialized='incremental',
    unique_key='(stablecoin_date, stablecoin_symbol)',
    on_schema_change='append_new_columns',
    cluster_by=['stablecoin_date'],
    incremental_strategy='merge'
) }}

with tx as (

    select * from {{ ref('transactions') }}
    where tx_category = 'stablecoin_transfer'
    {% if is_incremental() %}
      and block_timestamp >= (select dateadd('day', -3, max(stablecoin_date)) from {{ this }})
    {% endif %}

),

labeled as (

    select
          tx.tx_date                                       as stablecoin_date
        , case
            when tx.to_address = '0xdAC17F958D2ee523a2206206994597C13D831ec7' then 'USDT'
            when tx.to_address = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48' then 'USDC'
            else 'OTHER_STABLECOIN'
          end                                              as stablecoin_symbol
        , count(*)                                          as transfer_count
        , sum(tx.value_wei) / 1e6                           as transfer_volume_usd  -- USDT/USDC are 6 decimals
    from tx
    group by 1, 2

)

select * from labeled
