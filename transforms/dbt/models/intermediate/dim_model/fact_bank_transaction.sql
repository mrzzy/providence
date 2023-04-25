--
-- Providence
-- Transforms
-- DBT Intermediate: Bank Transaction Fact table
--
with
    keyed_transactions as (
        select
            {{
                dbt_utils.generate_surrogate_key(
                    ["account_no", "transacted_on", "description"]
                )
            }} as "id", *
        from {{ ref("stg_uob_statement") }}
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
    ),

    -- enrich transactions with account dimension
    enriched_transactions as (
        select t.*, a.id as account_id
        from unique_transactions as t
        left join {{ ref("dim_account") }} as a on a.vendor_id = t.account_no
    ),

    -- insert initial balance transaction so that sum of transaction amount will
    -- tally with account balance
    initial_balances as (
        select
            account_id,
            statement_begin,
            balance as balance,
            processed_on
        from ({{
            deduplicate(
                relation="enriched_transactions",
                partition_by="account_id",
                order_by="processed_on asc",
                n_row_col="_n_row_account",
            )
        }})
    ),

initial_transaction as (
        select
            {{ dbt_utils.generate_surrogate_key(["account_id"]) }} as "id",
            statement_begin as date_id,
            account_id,
            'Initial Balance' as description,
            processed_on as updated_at,
            balance as amount
        from initial_balances
    )

-- grain: 1 row = 1 bank transaction
select * from initial_transaction
union all
select
    id,
    transacted_on as date_id,
    account_id,
    description,
    processed_on as updated_at,
    deposit - withdrawal as amount
from enriched_transactions
