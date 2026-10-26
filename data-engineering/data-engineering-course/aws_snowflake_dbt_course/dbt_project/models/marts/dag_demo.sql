-- ============================================================================
-- models/marts/dag_demo.sql
-- ----------------------------------------------------------------------------
-- Demo model used in L46 "Creating a logical flow of models and
-- building clean DAGs". This model has 3 layers of dependencies so we
-- can visualize the dbt DAG with `dbt docs generate && dbt docs serve`.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

{{ config(materialized='view') }}

-- Layer 1: stg_ethereum__transactions (already exists in models/staging/)
-- Layer 2: this model (transactions, activity — already exist)
-- Layer 3: this view — depends on the layer-2 marts.

with activity as (
    select * from {{ ref('activity') }}
),

stablecoin as (
    select * from {{ ref('stablecoin_activity') }}
),

joined as (

    select
          a.activity_date
        , a.tx_category
        , a.tx_count
        , coalesce(s.transfer_count, 0)                  as stablecoin_transfer_count
        , coalesce(s.transfer_volume_usd, 0)             as stablecoin_transfer_volume_usd
    from activity a
    left join stablecoin s
        on a.activity_date = s.stablecoin_date

)

select * from joined
