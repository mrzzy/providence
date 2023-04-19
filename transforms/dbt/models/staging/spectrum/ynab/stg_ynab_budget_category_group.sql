--
-- Providence
-- Transforms
-- DBT Staging: YNAB budget category
--
select
    cast(g.id as varchar) as "id",
    cast(g.name as varchar) as "name",
    cast(g.deleted as boolean) as is_deleted,
    cast(s._ynab_src_scraped_on as timestamp) as scraped_on
from {{ source("ynab", "source_ynab") }} as s, s.category_groups as g
