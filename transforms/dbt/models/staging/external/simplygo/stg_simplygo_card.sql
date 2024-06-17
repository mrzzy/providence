--
-- Providence
-- Transforms
-- DBT Staging: Simplygo Cards
--
select
    cast(s.card_id as varchar) as "id",
    cast(s.card_name as varchar) as "name",
    {{ scraped_on("s") }} as scraped_on
from {{ source("simplygo", "simplygo_tfm") }} as s
