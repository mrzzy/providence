--
-- Providence
-- Transforms
-- DBT Analytics Bank Card Dimension
--
select id, name
from
    (
        {{
            dbt_utils.deduplicate(
                relation=ref("stg_simplygo_card"),
                partition_by="id",
                order_by="scraped_on desc",
            )
        }}
    )
