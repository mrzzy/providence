--
-- Providence
-- Transforms
-- DBT Staging: YNAB budget category
--

select
    cast(g.id as varchar) as "id",
    cast(g.name as varchar) as "name",
    cast(g.deleted as boolean) as is_deleted
from
