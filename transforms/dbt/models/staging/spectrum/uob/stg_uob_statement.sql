--
-- Providence
-- Transforms
-- DBT Staging: UOB Bank Account Transaction
--
select
    cast("transaction date" as date) as transacted_on,  -- noqa: RF05
    -- replace newlines in transaction description with spaces
    replace(
        cast("transaction description" as varchar),  -- noqa: RF05
        '\n',
        ' '
    ) as description,
    cast(withdrawal as decimal(10, 2)) as withdrawal,
    cast(deposit as decimal(10, 2)) as deposit,
    cast("available balance" as decimal(10, 2)) as balance,  -- noqa: RF05
    cast("account number" as varchar) as account_no,  -- noqa: RF05
    cast("account type" as varchar) as "name",  -- noqa: RF05
    cast(currency as varchar) as currency_code,
    -- split_part() is 1-indexed
    cast(
        split_part("statement period", ' To ', 1) as date  -- noqa: RF05
    ) as statement_begin,
    cast(
        split_part("statement period", ' To ', 2) as date  -- noqa: RF05
    ) as statement_end,
    coalesce(
        cast(_pandas_etl_transformed_on as timestamp), {{ timestamp_min() }}
    ) as processed_on
from {{ source("uob", "source_uob") }}
