--
-- Providence
-- Transforms
-- DBT Analytics: Accounting Transaction Fact table
--
with unique_transactions as (
    {{
        deduplicate(
            relation=ref("stg_ynab_transaction"),
            partition_by="id",
            order_by="scraped_on desc",
        )
    }}
),

unique_subtransactions as (
    {{
        deduplicate(
            relation=ref("stg_ynab_subtransaction"),
            partition_by="id",
            order_by="scraped_on desc",
        )
    }}
)

-- expand subtransactions as individual transaction rows
select
    s.super_id as super_id,
    t.budget_id,
    t.clearing_status,
    t.is_approved,
    t.account_id,
    "date" as date_id,
    coalesce(s.id, t.id) as "id",
    coalesce(s.description, t.description) as description,
    coalesce(s.category_id, t.category_id) as category_id,
    coalesce(s.payee_id, t.payee_id) as payee_id,
    coalesce(s.transfer_account_id, t.transfer_account_id) as transfer_account_id,
    coalesce(s.is_deleted, t.is_deleted) as is_deleted,
    coalesce(s.amount, t.amount) as amount,
    greatest(s.scraped_on, t.scraped_on) as updated_at
from unique_transactions as t
left join unique_subtransactions as s on s.super_id = t.id
