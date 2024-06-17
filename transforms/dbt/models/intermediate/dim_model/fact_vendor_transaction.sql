--
-- Providence
-- Transforms
-- DBT Intermediate: Bank Transaction Fact table
--
-- insert initial balance transaction so that sum of transaction amount will
-- tally with account balance
with
    initial_balances as (
        select account_id, statement_begin, balance, scraped_on
        from
            (
                {{
                    deduplicate(
                        relation=ref("int_unique_enriched_bank_statement"),
                        partition_by="account_id",
                        order_by="scraped_on asc",
                        n_row_col="_n_row_account",
                    )
                }}
            )
    ),

    initial_transaction as (
        select
            {{ dbt_utils.generate_surrogate_key(["account_id"]) }} as "id",
            statement_begin as date_id,
            account_id,
            'Initial Balance' as description,
            scraped_on as updated_at,
            balance as amount
        from initial_balances
    )

-- grain: 1 row = 1 bank transaction
select *
from initial_transaction
union all
select
    id,
    transacted_on as date_id,
    account_id,
    description,
    scraped_on as updated_at,
    deposit - withdrawal as amount
from {{ ref("int_unique_enriched_bank_statement") }}
