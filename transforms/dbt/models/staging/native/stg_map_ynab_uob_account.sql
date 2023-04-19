--
-- Providence
-- Transforms
-- DBT Staging: YNAB UOB Account Mapping
--
select distinct
    cast(budget_account_id as varchar) as budget_account_id,
    cast(vendor_id as varchar) as account_no
from {{ source("mapping", "map_account") }}
where vendor = 'UOB'
