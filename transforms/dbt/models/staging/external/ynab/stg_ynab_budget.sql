--
-- Providence
-- Transforms
-- DBT Staging: YNAB budget
--
select
    cast(s.data.budget.id as varchar) as "id",
    cast(s.data.budget.name as varchar) as "name",
    cast(s.data.budget.last_modified_on as timestamp) as modified_at,
    cast(s.data.budget.currency_format.iso_code as varchar) as currency_code,
    cast(s.data.budget.currency_format.currency_symbol as varchar) as currency_symbol,
    {{ scraped_on("s") }} as scraped_on
from {{ source("ynab", "ynab") }} as s
