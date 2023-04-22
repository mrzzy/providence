--
-- Providence
-- Transforms
-- DBT Staging: YNAB budget
--
select
    cast(id as varchar) as "id",
    cast(name as varchar) as "name",
    cast(last_modified_on as timestamp) as modified_at,
    cast(currency_format.iso_code as varchar) as currency_code,
    cast(currency_format.currency_symbol as varchar) as currency_symbol,
    cast(_ynab_src_scraped_on as timestamp) as scraped_on
from {{ source("ynab", "source_ynab") }}
