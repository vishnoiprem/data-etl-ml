-- ============================================================================
-- 01_section / code / stg_first_model.sql
-- ----------------------------------------------------------------------------
-- Stand-alone dbt staging model used to demonstrate Jinja rendering
-- without a Snowflake connection. Mirrors the pattern from
-- dbt_project/models/staging/stg_ethereum__transactions.sql.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

{{ config(materialized='view') }}

with source as (

    select * from {{ source('ethereum', 'raw_transactions') }}

),

renamed as (

    select
          hash                          as tx_hash
        , from_address
        , to_address
        , value / 1e18                  as value_eth
        , block_timestamp
    from source

)

select * from renamed
