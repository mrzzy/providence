--
-- Providence
-- Transforms
-- DBT Analytics: "Date" Dimension
--
select
    "date" as "id",
    "date",
    cast(to_char("date", 'W') as int) as week_of_month,
    cast(to_char("date", 'WW') as int) as week_of_year,
    cast(to_char("date", 'Q') as int) as "quarter",
    extract(day from "date") as day_of_month,
    extract(month from "date") as month_of_year,
    to_char("date", 'month') as month_name,
    to_char("date", 'mon') as month_short,
    extract(year from "date") as "year",
    extract(dayofweek from "date") as day_of_week,
    to_char("date", 'day') as weekday_name,
    to_char("date", 'dy') as weekday_short,
    extract(dayofyear from "date") as day_of_year,
    date_trunc('month', "date") as year_month,
    coalesce(extract(dayofweek from "date") in (0, 6), false) as is_weekend
from (
    -- generate next 20 years of date dimension rows
    {{
        dbt_utils.date_spline(
            datepart="day",
            start_date="cast('2019-01-01' as date)",
            end_date="cast(dateadd(year, 20, sysdate)) as date)"
        )
    }}
)
