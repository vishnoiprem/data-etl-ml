-- create_customers.sql — the CDC destination table.
--
-- Two things matter here beyond the column list:
--
--   1. The merge key (customer_id) is NOT NULL. A NULL key cannot be
--      matched by a MERGE, so a nullable merge key means some rows can
--      never be updated.
--
--   2. The table is CLUSTERed by the merge key. The merge sorts on the
--      key before matching, and clustering lets BigQuery skip the sort
--      and prune blocks. This is the single most effective BigQuery
--      optimisation for a CDC destination.
--
-- Run with:
--   bq query --use_legacy_sql=false < sql/create_customers.sql

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.datastream.customers` (
    customer_id STRING NOT NULL,
    first_name  STRING,
    last_name   STRING,
    email       STRING,
    region      STRING,
    tier        STRING,
    created_at  TIMESTAMP,
    ingested_at TIMESTAMP
)
PARTITION BY DATE(_PARTITIONTIME)
CLUSTER BY customer_id
OPTIONS (
    description = "Customers replicated by Google Cloud Datastream",
    labels = [
        ('source', 'datastream'),
        ('managed_by', 'terraform')
    ]
);
