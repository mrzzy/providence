--
-- Providence
-- Transforms
-- DBT Test: Sum of Bank Transaction amounts equate Bank Account balance
--
with
    expected_balances as (
        select account_id, balance, scraped_on
        from
            (
                {{
                    deduplicate(
                        relation=ref("int_unique_enriched_bank_statement"),
                        partition_by="account_id",
                        order_by="scraped_on desc",
                        n_row_col="_n_row_account",
                    )
                }}
            )
    ),

    actual_balances as (
        select account_id, sum(amount) as balance
        from {{ ref("fact_vendor_transaction") }}
        group by account_id
    )

select e.balance as expected, a.balance as actual
from expected_balances as e
left join actual_balances as a on a.account_id = e.account_id
where a.balance != a.balance
