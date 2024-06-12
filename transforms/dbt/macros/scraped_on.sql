--
-- Providence
-- Transforms
-- DBT Macros: YNAB Scraped On Column
--
-- Templates the scraped_on column for data derived from the YNAB data source.
-- relation: YNAB data source.
{% macro scraped_on(relation) -%}
coalesce(
    cast({{ relation }}."date" as timestamp), {{ timestamp_min() }}
)
{%- endmacro %}
