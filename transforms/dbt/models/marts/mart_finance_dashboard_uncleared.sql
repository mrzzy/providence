--
-- Providence
-- Transforms
-- DBT Marts: Finance Dashboard: Uncleared Transactions
--
with
    -- uncleared accounting transactions
    unreconciled_accounting as (
        select id, date_id, description, amount
        from {{ ref("fact_accounting_transaction") }}
        where clearing_status = 'uncleared'
    ),

    -- unreconciled vendor transactions:
    -- any transaction since account was last reconciled.
    unreconciled_vendor as (
        select t.id, t.date_id, t.description, t.amount
        from {{ ref("fact_vendor_transaction") }} as t
        left join {{ ref("dim_account") }} as a on a.id = t.account_id
        where t.date_id > a.last_reconciled_at
    )

select
    coalesce(a.date_id, v.date_id) as transaction_date,
    coalesce(a.description, v.description) as transaction_description,
    coalesce(a.amount, v.amount) as transaction_amount,
    (case when a.id is not null then '✔️' else '❌' end) as in_accounting,
    (case when v.id is not null then '✔️' else '❌' end) as in_vendor
-- join possible matchingg transactions by amount
from unreconciled_accounting as a
full join unreconciled_vendor as v on a.amount = v.amount
