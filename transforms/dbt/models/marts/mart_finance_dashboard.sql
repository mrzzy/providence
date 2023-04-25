--
-- Providence
-- Transforms
-- DBT Marts: Finance Dashboard
--
select
    d.year_month,
    -- transaction info
    t.amount as transaction_amount,
    t.date_id as transaction_date,
    a.is_cash as account_is_cash,
    -- income / spending
    (
        case
            when t.amount < 0 and t.transfer_account_id is null then t.amount else 0
        end
    ) as spending,
    (
        case
            when t.amount > 0 and t.transfer_account_id is null then t.amount else 0
        end
    ) as income
from {{ ref("fact_accounting_transaction") }} as t
left join {{ ref("dim_account") }} as a on a.id = t.account_id
left join {{ ref("dim_date") }} as d on d.id = t.date_id
