--
-- Providence
-- Transforms
-- DBT Analytics: Accounting Transaction Fact table
--

select
    {{ dbt_utils.star(ref("stg_ynab_transaction"), except=["date", "scraped_on"]) }},
    "date" as date_id,
    scraped_on as updated_at
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
