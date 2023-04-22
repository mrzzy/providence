--
-- Providence
-- Transforms
-- DBT Staging: YNAB Accounting Subtransaction
--
select
    cast(t.id as varchar) as "id",
    cast(t.transaction_id as varchar) as super_id,
    cast(t.memo as varchar) as description,
    cast(s.id as varchar) as budget_id,
    cast(t.category_id as varchar) as category_id,
    cast(t.payee_id as varchar) as payee_id,
    cast(t.transfer_account_id as varchar) as transfer_account_id,
    cast(t.deleted as boolean) as is_deleted,
    cast(s._ynab_src_scraped_on as timestamp) as scraped_on,
    -- ynab expresses amounts in milliunits: 1000 milliunits = $1
    cast(t.amount as decimal(13, 2)) / 1000 as amount
from {{ source("ynab", "source_ynab") }} as s, s.subtransactions as t
