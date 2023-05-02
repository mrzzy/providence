--
-- Providence
-- Transforms
-- DBT Staging: YNAB Budget Account Mapping
--
select
    {{ dbt_utils.generate_surrogate_key(["budget_account_id", "vendor", "vendor_id"]) }}
    as "id",
    cast(budget_account_id as varchar) as budget_account_id,
    cast(vendor as varchar) as vendor,
    cast(vendor_id as varchar) as vendor_id
from {{ source("mapping", "map_account") }}
