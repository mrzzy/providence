--
-- Providence
-- Transforms
-- DBT Marts: Finance Dashboard
--
select
  t.amount as transaction_amount,
  t.date_id as transaction_date,
  a.is_cash as account_is_cash
from {{ ref("fact_accounting_transaction") }} as t
left join {{ ref("dim_account") }} as a.id = t.account_id
