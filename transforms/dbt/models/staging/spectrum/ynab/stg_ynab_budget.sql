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
    coalesce(
        cast(s._rest_api_src_scraped_on as timestamp), {{ timestamp_min() }}
    ) as scraped_on
from {{ source("ynab", "source_ynab") }} as s
