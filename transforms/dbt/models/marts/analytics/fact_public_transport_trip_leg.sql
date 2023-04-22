--
-- Providence
-- Transforms
-- DBT Analytics: Public Transport Trip Legs Fact table
--
-- grain: 1 row = 1 trip leg
select
    -- since bank cards cannot make concurrent trips, the combination
    -- of travel timestamp & card_id should be unique for each trip leg
    {{ dbt_utils.generate_surrogate_key(["card_id", "traveled_on", "begin_at"]) }}
    as "id",
    {{
        dbt_utils.star(
            ref("stg_simplygo_trip_leg"),
            except=["traveled_on", "begin_at", "card_id"],
        )
    }},
    -- merged in travel timestamp in utc timezone
    convert_timezone('SGT', 'UTC', traveled_on + begin_at) as traveled_on,
    scraped_on as updated_at,
    -- foreign keys to dimensions
    traveled_on as travel_date_id,
    card_id as bank_card_id
from {{ ref("stg_simplygo_trip_leg") }}