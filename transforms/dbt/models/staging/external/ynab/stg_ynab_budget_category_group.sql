--
-- Providence
-- Transforms
-- DBT Staging: YNAB budget category groups
--
select
    cast(g.data.id as varchar) as "id",
    cast(g.data.name as varchar) as "name",
    cast(g.data.deleted as boolean) as is_deleted,
    {{ scraped_on("g") }} as scraped_on
from {{ ynab_unnest("data.budget.category_groups") }} as g
