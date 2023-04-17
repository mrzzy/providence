--
-- Providence
-- Transforms
-- DBT Analytics: Public Transport Trip Legs Fact table
--
-- grain: 1 row = 1 trip leg
with
    legs_merged_travel_on as (
        select
            {{
                dbt_utils.star(
                    ref("stg_simplygo_trip_leg"),
                    except=["traveled_on", "begin_at"],
                )
            }},
            -- merged in travel timestamp in utc timezone
            convert_timezone('SGT', 'UTC', traveled_on + begin_at) as traveled_on
        from {{ ref("stg_simplygo_trip_leg") }}
    )

select
    -- since bank cards cannot make concurrent trips, the combination
    -- of travel timestamp & card_id should be unique for each trip leg
    {{ dbt_utils.generate_surrogate_key(["card_id", "traveled_on"]) }} as "id",
    -- since bank cards cannot make concurrent trips, the combination
    -- of travel timestamp & card_id should be unique for each trip leg
    date_trunc('day', traveled_on) as travel_date_id,
    traveled_on,
    posting_ref,
    cost_sgd,
    source,
    destination,
    transport_mode,
    card_id as bank_card_id,
    scraped_on as updated_at
from legs_merged_travel_on
