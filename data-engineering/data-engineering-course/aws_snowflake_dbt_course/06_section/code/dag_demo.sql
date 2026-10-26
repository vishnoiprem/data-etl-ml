-- ============================================================================
-- 06_section / code / dag_demo.sql
-- ----------------------------------------------------------------------------
-- Stand-alone dbt model that joins 2 marts to demonstrate DAG construction.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

{{ config(materialized='view') }}

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
        , coalesce(s.transfer_count, 0)             as stablecoin_transfer_count
    from activity a
    left join stablecoin s
        on a.activity_date = s.stablecoin_date

)

select * from joined
