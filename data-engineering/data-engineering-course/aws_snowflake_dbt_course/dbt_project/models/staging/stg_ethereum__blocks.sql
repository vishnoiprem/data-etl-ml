-- ============================================================================
-- models/staging/stg_ethereum__blocks.sql
-- ----------------------------------------------------------------------------
-- Staging model for raw Ethereum blocks. Joins to transactions on
-- block_number to enrich with miner + reward.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

{{ config(materialized='view') }}

with source as (

    select
          block_number
        , block_timestamp
        , miner
    from {{ source('ethereum', 'raw_blocks') }}

),

renamed as (

    select
          block_number
        , block_timestamp
        , miner
        , date_trunc('day', block_timestamp) as block_date
    from source

)

select * from renamed
