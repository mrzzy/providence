--
-- Providence
-- Transforms
-- DBT Analytics: Date Dimension
--
with
    dates as (
        select date_trunc('day', scraped_on) as "date"
        from {{ ref("stg_simplygo_trip_leg") }}
        union
        select traveled_on as "date"
        from {{ ref("stg_simplygo_trip_leg") }}
    )
select
    "date" as id,
    "date",
    extract(day from "date") as day_of_month,
    extract(month from "date") as month_of_year,
    to_char("date", 'month') as month_name,
    to_char("date", 'mon') as month_short,
    extract(year from "date") as year,
    extract(dayofweek from "date") as day_of_week,
    to_char("date", 'day') as weekday_name,
    to_char("date", 'dy') as weekday_short,
    extract(dayofyear from "date") as day_of_year,
    cast(to_char("date", 'W') as int) as week_of_month,
    cast(to_char("date", 'WW') as int) as week_of_year,
    cast(to_char("date", 'Q') as int) as quarter,
    date_trunc('month', "date") as year_month,
    case
        -- 0: sunday, 6: saturday
        when extract(dayofweek from "date") in (0, 6) then true else false
    end as is_weekend
from dates
