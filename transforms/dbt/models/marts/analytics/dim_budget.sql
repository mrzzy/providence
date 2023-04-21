--
-- Providence
-- Transforms
-- DBT Analytics: Budget Dimension
--
select
    {{ dbt_utils.star(ref("stg_ynab_budget"), except=["scraped_on"]) }},
    scraped_on as updated_at
from
    (
        {{
            deduplicate(
                relation=ref("stg_ynab_budget"),
                partition_by="id",
                order_by="scraped_on desc",
            )
        }}
    )
