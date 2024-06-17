--
-- Providence
-- Transforms
-- DBT Intermediate: Budget Category dimension
--
-- use type 2 SCD to track changes to budget category's goals over time
with
    category_scd as (
        select
            *,
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

select
    c."id",
    c.category_id,
    c.name,
    c.budget_id,
    -- use unique_group's id instead to resolve dangling category_group_id as null
    g."id" as category_group_id,
    g.name as category_group,
    c.goal_type,
    c.goal_amount,
    c.goal_due,
    c.is_deleted,
    c.updated_at,
    c.effective_at,
    c.expired_at,
    coalesce(g.name like 'Expenses%', false) as is_expense,
    c.expired_at is null as is_current
from category_scd as c
left join unique_groups as g on c.category_group_id = g.id
