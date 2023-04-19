--
-- Providence
-- Transforms
-- DBT Staging: UOB Account
--

select distinct
  cast("account number" as varchar) as account_no,
  cast("account type" as varchar) as name,
  cast(currency as varchar) as currency_code
  -- split_part() is 1-indexed
  cast(split_part(statement_period, ' To ', 1) as date) as statement_begin,
  cast(split_part(statement_period, ' To ', 2) as date) as statement_end
from {{ source("uob", "source_uob") }}
