--
-- Providence
-- Transforms
-- DBT Staging: Simplygo Cards
--
select
    cast(c.id as varchar) as "id",
    cast(c.name as varchar) as "name",
    cast(s.scraped_on as timestamp) as scraped_on
from {{ source("simplygo", "simplygo_tfm") }} as s
