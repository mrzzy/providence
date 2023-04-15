--
-- Providence
-- Transforms
-- DBT Staging Simplygo Cards
--
-- vim:ft=sql.jinja2
select cast(c.id as varchar) as simplygo_id, cast(c.name as varchar) as name
from {{ source("simplygo", "source_simplygo") }} as s, s.cards as c
