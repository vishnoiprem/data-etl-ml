{# ===========================================================================
   macros/debug_helper.sql — debug helpers for dbt.
   ---------------------------------------------------------------------------
   Author: Prem Vishnoi <pvishnoi@avilx.com>

   Lecture reference: L77-L83 "Debugging". These macros wrap common
   debugging operations (print variable, query a relation, dump
   schema info).
   =========================================================================== #}

{% macro print_var(var_name) %}

    {% if execute %}
        {% set v = var(var_name) %}
        {{ log("Variable '" ~ var_name ~ "' = " ~ tojson(v), info=True) }}
    {% endif %}

{% endmacro %}


{% macro debug_relation(relation_name) %}

    {% if execute %}

        {% set rel = ref(relation_name) %}
        {{ log("Describing relation: " ~ rel, info=True) }}

        {% set sql %}
            describe table {{ rel }}
        {% endset %}

        {% set results = run_query(sql) %}
        {{ log("Schema: " ~ results.columns[0].values() | join(', '), info=True) }}

    {% endif %}

{% endmacro %}
