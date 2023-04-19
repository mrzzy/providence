--
-- Providence
-- Transforms
-- DBT Analytics: Payee Dimension
--

select
    {{ dbt_utils.star(ref("stg_ynab_payee"), except=["scraped_on"]) }},
    scraped_on as updated_at
from
    (
        {{
            dbt_utils.deduplicate(
                relation=ref("stg_ynab_payee"),
                partition_by="id",
                order_by="scraped_on desc",
            )
        }}
    )
