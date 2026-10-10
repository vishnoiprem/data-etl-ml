{# ===========================================================================
   05_section / code / log_macro_demo.sql
   ---------------------------------------------------------------------------
   Stand-alone dbt macro demo — used to show how to use {% if execute %}
   and {{ log() }} inside a macro.
   Author: Prem Vishnoi <pvishnoi@avilx.com>
   =========================================================================== #}

{% macro log_my_model(model_name) %}

    {% if execute %}
        {{ log("About to run model: " ~ model_name, info=True) }}
    {% endif %}

{% endmacro %}


{% macro count_rows(model_name) %}

    {% if execute %}

        {% set sql %}
            select count(*) as n from {{ ref(model_name) }}
        {% endset %}

        {% set results = run_query(sql) %}
        {% set row_count = results.columns[0].values()[0] %}
        {{ log("Model " ~ model_name ~ " has " ~ row_count ~ " rows", info=True) }}
        {{ return(row_count) }}

    {% endif %}

{% endmacro %}
