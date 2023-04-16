--
-- Providence
-- Transforms
-- DBT Staging Simplygo Public Transport Trip Legs
--
select
    cast(t.posting_ref as varchar) as posting_ref,
    cast(t.traveled_on as date) as traveled_on,
    cast(l.begin_at as time) as begin_at,
    cast(l.cost_sgd as decimal(4, 2)) as cost_sgd,
    cast(l.source as varchar) as source,
    cast(l.destination as varchar) as destination,
    cast(l."mode" as varchar) as transport_mode,
    cast(l.card_id as varchar) as card_id,
    cast(s.scraped_on as timestamp) as scraped_on,
from {{ source("simplygo", "source_simplygo") }} as s, s.trips as t, t.legs as l
