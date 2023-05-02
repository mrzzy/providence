--
-- Providence
-- Transforms
-- DBT Intermediate: Bank Card Dimension
--
with unique_cards as (
        {{
            deduplicate(
                relation=ref("stg_simplygo_card"),
                partition_by="id",
                order_by="scraped_on desc",
            )
        }}
    )

select c.id, c.name, a.id as account_id, c.scraped_on as updated_at
from unique_cards as c
