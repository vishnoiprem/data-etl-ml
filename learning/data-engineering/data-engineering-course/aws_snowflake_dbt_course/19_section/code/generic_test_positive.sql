-- ============================================================================
-- 19_section / code / generic_test_positive.sql
-- ----------------------------------------------------------------------------
-- Custom generic dbt test demo.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

{% test positive_value_demo(model, column_name) %}

    select *
    from {{ model }}
    where {{ column_name }} <= 0

{% endtest %}
