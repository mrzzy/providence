--
-- Providence
-- Transforms
-- DBT Staging: YNAB Payee
--

select
    cast(p.id as varchar) as "id",
    cast(p.name as varchar) as "name",
    cast(p.deleted as boolean) as is_deleted,
    cast(s._ynab_src_scraped_on as timestamp) as scraped_on
from {{ source("ynab", "source_ynab") }} as s, s.payees as p
