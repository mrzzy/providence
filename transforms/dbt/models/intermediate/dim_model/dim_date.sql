--
-- Providence
-- Transforms
-- DBT Intermediate: Date Dimension
--
select
    date_day as "id",
    date_day as "date",
    extract(weekofyear from date_day) as week_of_year,
    extract(quarter from date_day) as "quarter",
    date_trunc('week', date_day) as year_month_week,
    extract(day from date_day) as day_of_month,
    extract(dayofweek from date_day) as day_of_week,
    extract(dayofyear from date_day) as day_of_year,
    strftime(date_day, '%A') as weekday_name,
    strftime(date_day, '%a') as weekday_short,
    extract(month from date_day) as month_of_year,
    strftime(date_day, '%B') as month_name,
    strftime(date_day, '%b') as month_short,
    extract(year from date_day) as "year",
    date_trunc('month', date_day) as year_month,
    -- 0: sunday, 6: saturday
    coalesce(extract(dayofweek from date_day) in (0, 6), false) as is_weekend,
    current_date as updated_at
from
    (
        -- generate next 20 years of date dimension rows
        {{
            dbt_utils.date_spine(
                datepart="day",
                start_date="cast('2019-01-01' as date)",
                end_date="cast(current_date + interval 20 year as date)",
            )
        }}
    )
