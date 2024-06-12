--
-- Providence
-- Transforms
-- DBT Staging: YNAB Payee
--
select
    cast(p.data.id as varchar) as "id",
    cast(p.data.name as varchar) as "name",
    cast(p.data.deleted as boolean) as is_deleted,
    cast(p.data.transfer_account_id as varchar) as transfer_account_id,
    {{ scraped_on("p") }} as scraped_on
from {{ ynab_unnest("data.budget.payees") }} as p
