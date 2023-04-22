--
-- Providence
-- Transforms
-- DBT Macros: Deuplicate
--
-- Deduplicate the given relation by partitioning, ordering & picking the first row.
-- Custom implementation of deduplicate until the one in dbt-utils is fixed
-- https://github.com/dbt-labs/dbt-utils/issues/713
{% macro deduplicate(relation, partition_by, order_by) -%}
select *
from
    (
        select
            *,
            row_number() over (
                partition by {{ partition_by }} order by {{ order_by }}
            ) as _n_row
        from {{ relation }}
    )
where _n_row = 1
{%- endmacro %}
