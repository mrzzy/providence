--
-- Providence
-- Transforms
-- DBT Staging: YNAB Accounting Transaction
--
select t.*, {{ is_deleted("t") }} as is_deleted
from
    (
        select
            cast(t.data.id as varchar) as "id",
            cast(t.data.cleared as varchar) as clearing_status,
            cast(t.data.approved as boolean) as is_approved,
            cast(t.budget_id as varchar) as budget_id,
            cast(t.data.category_id as varchar) as category_id,
            cast(t.data.account_id as varchar) as account_id,
            cast(t.data.payee_id as varchar) as payee_id,
            cast(t.data.transfer_account_id as varchar) as transfer_account_id,
            cast(t.data."date" as date) as "date",
            lower(
                regexp_replace(trim(cast(t.data.memo as varchar)), ' +', ' ')
            ) as description,
            {{ scraped_on("t") }} as scraped_on,
            -- ynab expresses amounts in milliunits: 1000 milliunits = $1
            cast(t.data.amount as decimal(13, 2)) / 1000 as amount,
            cast(t.data.matched_transaction_id as varchar) as matched_transaction_id
        from {{ ynab_unnest("data.budget.transactions") }} as t
    ) as t
