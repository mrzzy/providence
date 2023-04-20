--
-- Providence
-- Transforms
-- DBT Staging: UOB Account
--
select
    cast("account number" as varchar) as account_no,  -- noqa: RF05
    cast("account type" as varchar) as "name",  -- noqa: RF05
    cast(currency as varchar) as currency_code,
    -- split_part() is 1-indexed
    cast(
        split_part("statement period", ' To ', 1) as date  -- noqa: RF05
    ) as statement_begin,
    cast(
        split_part("statement period", ' To ', 2) as date  -- noqa: RF05
    ) as statement_end
from {{ source("uob", "source_uob") }}
