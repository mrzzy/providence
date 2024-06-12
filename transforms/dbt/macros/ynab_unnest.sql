--
-- Providence
-- Transforms
-- DBT Macros: Unnest YNAB data
--
-- Replicates common query pattern from source YNAB budget data: 
-- unnest some data column while retaining the budget_id & date field in the table.
-- Unnested column accessible as as 'data' in the returned table.
{% macro ynab_unnest(unnest_col, date_col="date") -%}
(
    select 
        unnest(s.{{ unnest_col }}) as data, 
        s.data.budget.id as budget_id,
        s.{{ date_col }} as "date"
    from {{ source("ynab", "ynab") }} as s
)
{%- endmacro %}
