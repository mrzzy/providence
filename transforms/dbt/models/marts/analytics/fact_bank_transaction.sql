--
-- Providence
-- Transforms
-- DBT Analytics: Bank Transaction Fact table
--
with
    keyed_transactions as (
        select
            {{
                dbt_utils.generate_surrogate_key(
                    ["account_no", "transacted_on", "description"]
                )
            }} as "id", *
        from {{ ref("stg_uob_transaction") }}
    ),

    unique_transactions as (
        (
            {{
                deduplicate(
                    relation="keyed_transactions",
                    partition_by="id",
                    order_by="processed_on desc",
                )
            }}
        )
    )

select
    t.id,
    t.transacted_on as date_id,
    a.id as account_id,
    t.description,
    t.processed_on as updated_at,
    t.deposit - t.withdrawal as amount
from unique_transactions as t
left join dim_account as a on a.vendor_id = t.account_no
