--
-- Providence
-- Transforms
-- DBT Staging: Simplygo Public Transport Trip Legs
--
select
    cast(s.posting_ref as varchar) as posting_ref,
    cast(s.traveled_on as timestamp) as traveled_on,
    cast(
        case s.cost_sgd when 'Pass Usage' then '0.00' else s.cost_sgd end as decimal(
            4, 2
        )
    ) as cost_sgd,
    cast(s.source as varchar) as "source",
    cast(s.destination as varchar) as destination,
    cast(s.trip_id as varchar) as trip_id,
    cast(s.mode as varchar) as transport_mode,
    cast(s.card_id as varchar) as card_id,
    {{ scraped_on("s") }} as scraped_on
from {{ source("simplygo", "simplygo_tfm") }} as s
