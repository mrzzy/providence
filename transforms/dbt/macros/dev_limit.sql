--
-- Providence
-- Transforms
-- DBT Macros: Dev Limit
--
-- Apply a row limit to speed up development model builds.
{% macro dev_limit() -%}
    {% if target.name == "dev" -%} limit {{ var("dev_limit_n_rows", 100) }} {%- endif %}
{%- endmacro %}
