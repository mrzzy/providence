--
-- Providence
-- Transforms
-- DBT Staging: YNAB Accounting Subtransaction
--
select t.*, {{ is_deleted("t") }} as is_deleted
from
    (
        select
            cast(t.data.id as varchar) as "id",
            cast(t.data.transaction_id as varchar) as super_id,
            cast(t.data.memo as varchar) as description,
            cast(t.budget_id as varchar) as budget_id,
            cast(t.data.category_id as varchar) as category_id,
            cast(t.data.payee_id as varchar) as payee_id,
            cast(t.data.transfer_account_id as varchar) as transfer_account_id,
            {{ scraped_on("t") }} as scraped_on,
            -- ynab expresses amounts in milliunits: 1000 milliunits = $1
            cast(t.data.amount as decimal(13, 2)) / 1000 as amount
        from {{ ynab_unnest("data.budget.subtransactions") }} as t
    ) as t
