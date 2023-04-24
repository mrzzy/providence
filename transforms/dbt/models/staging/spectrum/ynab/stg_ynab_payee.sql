--
-- Providence
-- Transforms
-- DBT Staging: YNAB Payee
--
select
    cast(p.id as varchar) as "id",
    cast(p.name as varchar) as "name",
    cast(p.deleted as boolean) as is_deleted,
    cast(p.transfer_account_id as varchar) as transfer_account_id,
    coalesce(
        cast(s._ynab_src_scraped_on as timestamp), {{ timestamp_min() }}
    ) as scraped_on
from {{ source("ynab", "source_ynab") }} as s, s.payees as p
