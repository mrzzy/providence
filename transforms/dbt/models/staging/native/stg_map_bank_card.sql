--
-- Providence
-- Transforms
-- DBT Staging: Bank Card-Account Mapping
--
select

    {{ dbt_utils.generate_surrogate_key(["bank_card_id", "vendor", "vendor_id"]) }}
    as "id",
    cast(bank_card_id as varchar) as bank_card_id,
    cast(vendor as varchar) as vendor,
    cast(vendor_id as varchar) as vendor_id
from {{ source("mapping", "map_bank_card") }}
