{# ===========================================================================
   macros/dry_refactor.sql — DRY macro for repeated CTEs.
   ---------------------------------------------------------------------------
   Author: Prem Vishnoi <pvishnoi@avilx.com>

   Lecture reference: L37 "Advanced Macros: run_query()",
   L38 "Advanced Macros: if execute & return()".
   Demonstrates how to extract a common CTE into a macro so multiple
   models can reuse it.
   =========================================================================== #}

{% macro cents_to_dollars(column_name, decimals=18) -%}

    cast({{ column_name }} as numeric(38, {{ decimals }})) / 1e{{ decimals }}

{%- endmacro %}


{% macro filter_incremental(this_relation, date_column) -%}

    {% if is_incremental() -%}

        where {{ date_column }} >= (
            select dateadd('day', -3, max({{ date_column }}))
            from {{ this_relation }}
        )

    {%- endif %}

{%- endmacro %}
