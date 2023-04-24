--
-- Providence
-- Transforms
-- DBT Intermediate: Date Dimension
--
select
    date_day as "id",
    date_day as "date",
    cast(to_char(date_day, 'W') as int) as week_of_month,
    cast(to_char(date_day, 'WW') as int) as week_of_year,
    cast(to_char(date_day, 'Q') as int) as "quarter",
    extract(day from date_day) as day_of_month,
    extract(dayofweek from date_day) as day_of_week,
    extract(dayofyear from date_day) as day_of_year,
    to_char(date_day, 'day') as weekday_name,
    to_char(date_day, 'dy') as weekday_short,
    extract(month from date_day) as month_of_year,
    to_char(date_day, 'month') as month_name,
    to_char(date_day, 'mon') as month_short,
    extract(year from date_day) as "year",
    date_trunc('month', date_day) as year_month,
    -- 0: sunday, 6: saturday
    coalesce(extract(dayofweek from date_day) in (0, 6), false) as is_weekend,
    date_trunc('day', sysdate) as updated_at
from
    (
        -- generate next 20 years of date dimension rows
        {{
            dbt_utils.date_spine(
                datepart="day",
                start_date="cast('2019-01-01' as date)",
                end_date="cast(dateadd(year, 20, sysdate) as date)",
            )
        }}
    )
