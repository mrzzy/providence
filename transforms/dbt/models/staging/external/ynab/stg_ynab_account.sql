--
-- Providence
-- Transforms
-- DBT Analytics: YNAB Budget Account
--
select
    cast(a.data.id as varchar) as "id",
    cast(a.data.name as varchar) as "name",
    cast(a.data."type" as varchar) as "type",
    cast(a.data.on_budget as boolean) as on_budget,
    cast(a.data.closed as boolean) as is_closed,
    cast(a.data.deleted as boolean) as is_deleted,
    cast(a.data.transfer_payee_id as varchar) as payee_id,
    cast(a.data.last_reconciled_at as timestamp) as last_reconciled_at,
    {{ scraped_on("a") }} as scraped_on
from {{ ynab_unnest("data.budget.accounts") }} as a
