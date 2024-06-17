--
-- Providence
-- Transforms
-- DBT Macros: Deuplicate
--
-- Deduplicate the given relation by partitioning, ordering & picking the first row.
-- Custom implementation of deduplicate for duckdb
{% macro deduplicate(relation, partition_by, order_by, n_row_col="n_row") -%}
    select distinct on ({{ partition_by }}) *
    from {{ relation }} as tt
    order by {{ order_by }}
{%- endmacro %}
