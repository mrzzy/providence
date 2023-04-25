--
-- Providence
-- Transforms
-- DBT Marts: Finance Dashboard
--
select amount as transaction_amount, date_id as transaction_date
from {{ ref("fact_accounting_transaction") }}
