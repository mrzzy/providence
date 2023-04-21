--
-- Providence
-- Transforms
-- DBT Analytics: Budget Category dimension
--
-- use type 2 SCD to track changes to budget category's goals over time
with
    category_scd as (
        select
            {{
                dbt_utils.star(
                    ref("int_unique_budget_category"),
                    except=["budget_month", "budgeted_amount"],
                )
            }},
            cast(budget_month as timestamp) as effective_at,
            -- dimension row expire when the next dimension row becomes effective
            coalesce(
                cast(
                    lead(budget_month) over (
                        partition by category_id order by budget_month asc
                    ) as timestamp
                ),
                {{ timestamp_max() }}
            ) as expired_at
        from {{ ref("int_unique_budget_category") }}
    ),

    unique_groups as (
        {{
            deduplicate(
                relation=ref("stg_ynab_budget_category_group"),
                partition_by="id",
                order_by="scraped_on desc",
            )
        }}
    )

select c.*, g.name as category_group, c.expired_at is null as is_current
from category_scd as c
inner join unique_groups as g on g.id = c.category_group_id
