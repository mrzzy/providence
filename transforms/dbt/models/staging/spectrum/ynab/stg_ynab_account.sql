--
-- Providence
-- Transforms
-- DBT Analytics: YNAB Budget Account
--
select
    cast(a.id as varchar) as "id",
    cast(a.name as varchar) as "name",
    cast(a."type" as varchar) as "type",
    cast(a.on_budget as boolean) as on_budget,
    cast(a.closed as boolean) as is_closed,
    cast(a.deleted as boolean) as is_deleted,
    cast(a.transfer_payee_id as varchar) as payee_id,
    coalesce(
        cast(s._ynab_src_scraped_on as timestamp), {{ timestamp_min() }}
    ) as scraped_on
from {{ source("ynab", "source_ynab") }} as s, s.accounts as a
