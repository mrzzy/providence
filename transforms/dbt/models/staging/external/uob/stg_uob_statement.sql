--
-- Providence
-- Transforms
-- DBT Staging: UOB Bank Account Transaction
--
{% set date_fmt = "%d %b %Y" %}
select
    strptime(s."transaction date", '{{ date_fmt }}') as transacted_on,  -- noqa: RF05
    -- replace newlines in transaction description with spaces
    replace(
        cast(s."transaction description" as varchar),  -- noqa: RF05
        '\n',
        ' '
    ) as description,
    cast(s.withdrawal as decimal(10, 2)) as withdrawal,
    cast(s.deposit as decimal(10, 2)) as deposit,
    cast(s."available balance" as decimal(10, 2)) as balance,  -- noqa: RF05
    cast(s."account number" as varchar) as account_no,  -- noqa: RF05
    cast(s."account type" as varchar) as "name",  -- noqa: RF05
    cast(s.currency as varchar) as currency_code,
    -- split_part() is 1-indexed
    strptime(
        split_part(s."statement period", ' To ', 1), '{{ date_fmt }}'  -- noqa: RF05
    ) as statement_begin,  -- noqa: RF05
    strptime(
        split_part(s."statement period", ' To ', 2), '{{ date_fmt }}'  -- noqa: RF05
    ) as statement_end,  -- noqa: RF05
    {{ scraped_on("s") }} as scraped_on
from {{ source("uob", "uob") }} as s
