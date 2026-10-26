-- ============================================================================
-- models/staging/stg_ethereum__transactions.sql
-- ----------------------------------------------------------------------------
-- Staging model for raw Ethereum transactions.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
--
-- Renames raw columns to a project-wide standard, casts types, and adds
-- derived columns. ALL staging models in this project follow the same
-- `stg_<source>__<table>` naming convention so we can identify which
-- upstream source each staging model shields.
-- ============================================================================

{{ config(materialized='view') }}

with source as (

    select
          hash
        , from_address
        , to_address
        , value
        , block_timestamp
        , gas_used
        , gas_price
        , block_number
    from {{ source('ethereum', 'raw_transactions') }}

),

renamed as (

    select
          hash                                           as tx_hash
        , from_address                                   as from_address
        , to_address                                     as to_address
        , value                                          as value_wei
        , block_timestamp                                as block_timestamp
        , gas_used                                       as gas_used
        , gas_price                                      as gas_price_wei
        , block_number                                   as block_number
        -- Derived columns used by downstream marts
        , value / 1e18                                   as value_eth
        , gas_used * gas_price / 1e18                    as tx_fee_eth
        , date_trunc('day', block_timestamp)             as tx_date
    from source

)

select * from renamed
