--
-- Providence
-- Transforms
-- DBT Staging: YNAB Accounting Transaction
--
select
    -- ynab api does not include deleted transactions in non-delta, full budget
    -- requests
    -- assume transactions that we can no longer scrape in newer requests as deleted
    *, datediff(day, t.scraped_on, sysdate) > 2 as is_deleted
from
    (
        select
            cast(t.id as varchar) as "id",
            cast(t.cleared as varchar) as clearing_status,
            cast(t.approved as boolean) as is_approved,
            cast(s.data.budget.id as varchar) as budget_id,
            cast(t.category_id as varchar) as category_id,
            cast(t.account_id as varchar) as account_id,
            cast(t.payee_id as varchar) as payee_id,
            cast(t.transfer_account_id as varchar) as transfer_account_id,
            cast(t.date as date) as "date",
            lower(
                regexp_replace(trim(cast(t.memo as varchar)), ' +', ' ')
            ) as description,
            coalesce(
                cast(s._rest_api_src_scraped_on as timestamp), {{ timestamp_min() }}
            ) as scraped_on,
            -- ynab expresses amounts in milliunits: 1000 milliunits = $1
            cast(t.amount as decimal(13, 2)) / 1000 as amount
        from {{ source("ynab", "source_ynab") }} as s, s.data.budget.transactions as t
    ) as t
