-- ============================================================================
-- models/marts/transactions.sql
-- ----------------------------------------------------------------------------
-- Mart model: one row per Ethereum transaction, enriched with category.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
--
-- Lecture reference: L16 "Building an Enriched Transactions Model",
-- L18 "Categorizing Ethereum Transactions".
--
-- Uses staging models from models/staging/* (never raw tables directly)
-- — this is the "shielding with staging models" pattern from L22.
-- ============================================================================

{{ config(
    materialized='incremental',
    unique_key='tx_hash',
    on_schema_change='append_new_columns',
    incremental_strategy='merge'
) }}

with tx as (

    select * from {{ ref('stg_ethereum__transactions') }}
    {% if is_incremental() %}
      where block_timestamp >= (select dateadd('day', -3, max(block_timestamp)) from {{ this }})
    {% endif %}

),

stablecoins as (

    select address_value from (
        {% for addr in var('stablecoin_addresses') %}
          select '{{ addr }}' as address_value {% if not loop.last %}union all{% endif %}
        {% endfor %}
    )

),

categorized as (

    select
          tx.tx_hash
        , tx.from_address
        , tx.to_address
        , tx.value_wei
        , tx.value_eth
        , tx.tx_fee_eth
        , tx.gas_used
        , tx.gas_price_wei
        , tx.block_timestamp
        , tx.block_number
        , tx.tx_date
        -- Categorization: stablecoin transfer, contract call, plain ETH, contract creation (NULL to_address)
        , case
            when tx.to_address is null                                        then 'contract_creation'
            when tx.to_address in (select address_value from stablecoins)     then 'stablecoin_transfer'
            when tx.value_eth > 0                                            then 'eth_transfer'
            else 'contract_call'
          end as tx_category
    from tx

)

select * from categorized
