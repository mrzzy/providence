--
-- Providence
-- Transforms
-- DBT Macros: Timestamp Max
--

{% macro timestamp_max() -%}
cast('9999-12-31 23:59:59' as timestamp)
{%- endmacro %}
