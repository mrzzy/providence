--
-- Providence
-- Transforms
-- DBT Intermediate: Public Transport Trip Legs Facts
--
-- grain: 1 row = 1 trip leg snapshot
with
    trip_legs_duplicated as (
        select
            -- since bank cards cannot make concurrent trips, the combination
            -- of travel timestamp & card_id should be unique for each trip leg
            {{
                dbt_utils.generate_surrogate_key(
                    ["card_id", "traveled_on", "begin_at"]
                )
            }} as "id",
            {{
                dbt_utils.star(
                    ref("stg_simplygo_trip_leg"),
                    except=["traveled_on", "begin_at", "card_id", "posting_ref"],
                )
            }},
            posting_ref as billing_ref,
            posting_ref is not null as is_billed,
            -- merged in travel timestamp in utc timezone
            convert_timezone('SGT', 'UTC', traveled_on + begin_at) as traveled_on,
            scraped_on as updated_at,
            -- foreign keys to dimensions
            traveled_on as travel_date_id,
            card_id as bank_card_id
        from {{ ref("stg_simplygo_trip_leg") }}
    ),

    unique_trip_legs as (
        {{
            deduplicate(
                relation="trip_legs_duplicated",
                partition_by="id",
                order_by="updated_at desc",
            )
        }}
    )

select t.*, a.id as account_id
-- associate trip leg with bank account based on bank account used to pay for the leg
from unique_trip_legs as t
left join {{ ref("stg_map_bank_card") }} as m on m.bank_card_id = t.bank_card_id
left join
    {{ ref("dim_account") }} as a on m.vendor = a.vendor and m.vendor_id = a.vendor_id
