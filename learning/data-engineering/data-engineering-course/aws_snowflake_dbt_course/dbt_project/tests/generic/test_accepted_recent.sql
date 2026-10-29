-- ============================================================================
-- tests/generic/test_accepted_recent.sql
-- ----------------------------------------------------------------------------
-- Custom generic test that asserts a date column is within the last N days.
-- Author: Prem Vishnoi <pvishnoi@avilx.com>
-- ============================================================================

{% test accepted_recent(model, column_name, days=7) %}

    select *
    from {{ model }}
    where {{ column_name }} < dateadd('day', -{{ days }}, current_timestamp)

{% endtest %}
