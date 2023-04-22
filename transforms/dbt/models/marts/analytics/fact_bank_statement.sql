--
-- Providence
-- Transforms
-- DBT Analytics: Bank Statement Fact table
--
with
    keyed_statement as (
        select
            {{
                dbt_utils.generate_surrogate_key(
                    ["statement_begin", "statement_begin"]
                )
            }} as "id", *
        from {{ ref("stg_uob_statement") }}
    ),

    unique_statement as (
        {{
            deduplicate(
                relation="keyed_statement",
                partition_by="id",
                order_by="processed_on desc",
            )
        }}
    )

-- grain: 1 row = 1 bank statement
select
    s.id,
    s.statement_begin as begin_date_id,
    s.statement_end as end_date_id,
    a.id as account_id,
    s.balance,
    s.processed_on as updated_at
from unique_statement as s
left join {{ ref("dim_account") }} as a on a.vendor_id = s.account_no
