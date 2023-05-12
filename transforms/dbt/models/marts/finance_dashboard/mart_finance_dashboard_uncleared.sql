--
-- Providence
-- Transforms
-- DBT Marts: Finance Dashboard: Uncleared Transactions
--
with
    -- uncleared accounting transactions
    unreconciled_accounting as (
        -- full transactions
        select id, date_id, account_id, description, amount
        from {{ ref("fact_accounting_transaction") }}
        where t.clearing_status = 'uncleared' and super_id is null
        union all
        -- split transactions composed of multiple subtransactions
        -- each split transaction will be 1 transaction on the vendor account side
        -- group subtransactions into split transactions better matching by amount.
        select
            t.id,
            t."date" as date_id,
            t.account_id,
            t.description,
            sum(t.amount) as amount
        from {{ ref("int_unique_transaction") }} as t
        inner join
            (
                select distinct super_id from {{ ref("fact_accounting_transaction") }}
            ) as s
            on s.super_id = t.id
        where t.clearing_status = 'uncleared'
        group by t.id, t."date", t.account_id, t.description
    ),

    -- unreconciled vendor transactions:
    -- any transaction since account was last reconciled.
    unreconciled_vendor as (
        select t.id, t.date_id, t.account_id, t.description, t.amount
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
-- join possible matching transactions by amount
from unreconciled_accounting as a
full join
    unreconciled_vendor as v on a.account_id = v.account_id and a.amount = v.amount
