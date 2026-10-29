-- ============================================================================
-- tests/generic/test_positive_value.sql
-- ----------------------------------------------------------------------------
-- Custom generic dbt test that asserts a column has all positive values.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
--
-- Lecture reference: L107 "Custom data tests - Overriding built-in tests".
-- A generic test returns rows that *fail* the test. dbt raises an
-- error if the query returns 1+ rows.
-- ============================================================================

{% test positive_value(model, column_name) %}

    select *
    from {{ model }}
    where {{ column_name }} <= 0

{% endtest %}
