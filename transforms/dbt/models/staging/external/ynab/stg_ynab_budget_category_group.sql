--
-- Providence
-- Transforms
-- DBT Staging: YNAB budget category
--
select
    cast(g.id as varchar) as "id",
    cast(g.name as varchar) as "name",
    cast(g.deleted as boolean) as is_deleted,
    coalesce(
        cast(s._rest_api_src_scraped_on as timestamp), {{ timestamp_min() }}
    ) as scraped_on
from {{ source("ynab", "source_ynab") }} as s, s.data.budget.category_groups as g
