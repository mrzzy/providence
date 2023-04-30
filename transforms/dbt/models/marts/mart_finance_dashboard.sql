--
-- Providence
-- Transforms
-- DBT Marts: Finance Dashboard
--
select
    d.year_month,
    d.year_month_week,
    -- transaction
    t.amount as transaction_amount,
    (case when a.is_cash then t.amount else 0 end) as cash_amount,
    t.date_id as transaction_date,
    t.description as transaction_description,
    t.transfer_account_id is not null as transaction_is_transfer,
    t.clearing_status as transaction_clearing_status,
    -- account
    a.is_cash as account_is_cash,
    -- category
    c.category_group_id as budget_category_group_id,
    coalesce(c.category_group, 'Unknown Category Group') as budget_category_group,
    coalesce(c.name, 'Unknown Category') as budget_category,
    coalesce(c.is_expense, false) as budget_is_expense,
    -- payee
    coalesce(p.name, 'Unknown Payee') as payee_name,
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
left join {{ ref("dim_budget_category") }} as c on c.id = t.category_id
left join {{ ref("dim_payee") }} as p on p.id = t.payee_id
