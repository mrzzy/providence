--
-- Providence
-- Transforms
-- DBT Marts: Finance Dashboard
--
select
    d.year_month,
    d.year_month_week,
    -- transaction info
    t.amount as transaction_amount,
    (case when a.is_cash then t.amount else 0 end) as cash_amount,
    t.date_id as transaction_date,
    t.description as transaction_description,
    a.is_cash as account_is_cash,
    -- spending
    (
        case
            when t.amount < 0 and t.transfer_account_id is null and a.is_cash then t.amount else 0
        end
    ) as spending,
    coalesce(p.is_unaccounted, false) as is_unaccounted,
    -- income
    (
        case
            when t.amount > 0 and t.transfer_account_id is null and a.is_cash then t.amount else 0
        end
    ) as income,
    coalesce(p.is_passive, false) as is_passive
from {{ ref("fact_accounting_transaction") }} as t
left join {{ ref("dim_account") }} as a on a.id = t.account_id
left join {{ ref("dim_date") }} as d on d.id = t.date_id
left join {{ ref("dim_payee") }} as p on p.id = t.payee_id
