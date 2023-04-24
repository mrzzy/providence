--
-- Providence
-- Transforms
-- DBT Macros: Timestamp Min/Max,
--
{% macro timestamp_max() -%} cast('9999-12-31 23:59:59' as timestamp) {%- endmacro %}
{% macro timestamp_min() -%} cast('0001-01-01 00:00:00' as timestamp) {%- endmacro %}
