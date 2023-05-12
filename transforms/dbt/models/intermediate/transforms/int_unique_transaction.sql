--
-- Providence
-- Transforms
-- DBT Intermediate: Unique Accounting Transactions
--
select *
from
    (
        {{
            deduplicate(
                relation=ref("stg_ynab_transaction"),
                partition_by="id",
                order_by="scraped_on desc",
            )
        }}
    )
where is_deleted = false
