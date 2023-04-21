--
-- Providence
-- Transforms
-- DBT Analytics: Budget Category dimension
--


-- use type 2 SCD to track changes to budget category's goals over time
with
    duplicated_categories as (
        select
            {{ dbt_utils.generate_surrogate_key(["id", "budget_month"]) }}
            as "id",
            id as category_id,
            {{
                dbt_utils.star(
                    ref("stg_ynab_budget_category"),
                    except=["id", "budget_month", "budgeted"],
                )
            }},
            scraped_on as updated_at,
            cast(budget_month as timestamp) as effective_at
        from {{ ref("stg_ynab_budget_category") }}
    ),

unique_categories as (
        select *,
        coalesce(
            lead(effective_at) over (partition by category_id order by effective_at asc),
            {{ timestamp_max() }}
        ) as expired_at
        from (
        {{
            deduplicate(
                relation="duplicated_categories",
                partition_by="id",
                order_by="updated_at desc",
            )
        }}
    )
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
    c.*,
    c.expired_at is null as is_current,
    g.name as category_group
from unique_categories as c
inner join unique_groups as g on g.id = c.category_group_id
