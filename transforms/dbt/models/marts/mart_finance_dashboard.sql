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
    -- TODO(mrzzy): pushdown is_passive, is_unaccounted to fact_accounting_transaction
    -- spending
    (
        case
            when t.amount < 0 and t.transfer_account_id is null and a.is_cash then t.amount else 0
        end
    ) as spending,
    -- unaccounted Spending: any spending associated with the adjustment payee
    coalesce(
        p.id in (
            '10339a7c-b54b-46a8-9141-a793d5bdfb1a',  -- Manual Balance Adjustment
            '11e89a59-2f9c-4b76-9af9-3baf57eb7a18'  -- Reconciliation Balance Adjustment
        ),
        -- consider no assigned payee as unaccounted spending
        true
    ) as is_unaccounted,
    -- income
    (
        case
            when t.amount > 0 and t.transfer_account_id is null and a.is_cash then t.amount else 0
        end
    ) as income,
    -- passive income: any income derived from the following financial institution
    coalesce(
        p.id in (
            '3304a058-a21e-4dd6-8545-1f19102f8f9a',  -- Standard Charted Bank
            '376c5870-56ca-46f5-b1f2-7a2ebf5dadf3',  -- UOB Bank
            '05eae682-21f0-4fb9-8dcb-da72963fa5d5',  -- SG Government: CPF
            '99d50734-caa5-4638-a0bc-d8941a7984ff'  -- Central Depository
        ),
        -- default to assigning non passive categorisation if no payee is attached.
        false
    ) as is_passive
from {{ ref("fact_accounting_transaction") }} as t
left join {{ ref("dim_account") }} as a on a.id = t.account_id
left join {{ ref("dim_date") }} as d on d.id = t.date_id
left join {{ ref("dim_payee") }} as p on p.id = t.payee_id
