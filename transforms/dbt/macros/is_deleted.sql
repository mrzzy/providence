--
-- Providence
-- Transforms
-- DBT Macros: Is Deleted Herustic
--
-- Templates the is_deleted column based on the Is Deleted Herustic.
-- YNAB API does not include deleted transactions in non-delta, full budget requests.
-- Assume transactions that we can no longer scrape in newer requests as deleted
-- relation: containing scraped_on column to derive is_deleted from.
{% macro is_deleted(relation) -%}
datediff('day', {{ relation }}.scraped_on, current_date) > 2
{%- endmacro %}
