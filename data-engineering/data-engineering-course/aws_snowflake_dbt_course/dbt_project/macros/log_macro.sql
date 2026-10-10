{# ===========================================================================
   macros/log_macro.sql — macro that emits a `DO $$ ... $$` log block.
   ---------------------------------------------------------------------------
   Author: Prem Vishnoi <pvishnoi@avilx.com>

   Lecture reference: L36 "Advanced Macros: Execution & Logging".
   Demonstrates:
     - Macro dispatch with `{% if execute %}`
     - Logging via `{{ log(...) }}` (printed at parse time)
     - Returning a runnable SQL block
   =========================================================================== #}

{% macro log_model_run(model_name, row_count) %}

  {% if execute %}

    {{ log("Running model: " ~ model_name ~ " (" ~ row_count ~ " rows)", info=True) }}

    {% set sql %}

      -- Snowflake doesn't have a `DO` block, so we use SELECT ... DUMMY:
      select 'Ran ' || '{{ model_name }}' || ' with ' || {{ row_count }} || ' rows' as log_line
      from (select 1 as dummy) x

    {% endset %}

    {% do run_query(sql) %}

  {% endif %}

{% endmacro %}
