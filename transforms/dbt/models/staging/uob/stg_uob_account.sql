--
-- Providence
-- Transforms
-- DBT Staging: UOB Account
--

select distinct
  cast("account number" as varchar) as account_no,
  cast("account type" as varchar) as name,
  cast(currency as varchar) as currency_code
from {{ source("uob", "source_uob") }}
