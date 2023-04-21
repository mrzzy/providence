--
-- Providence
-- Transforms
-- DBT Intermediate: Unique Budget Categories
--
with
    duplicated_categories as (
        select
            {{ dbt_utils.generate_surrogate_key(["id", "budget_month"]) }} as "id",
            id as category_id,
            scraped_on as updated_at,
            {{
                dbt_utils.star(
                    ref("stg_ynab_budget_category"),
                    except=["id", "scraped_on"],
                )
            }}
        from {{ ref("stg_ynab_budget_category") }}
    )
select *
from
    (
        {{
            deduplicate(
                relation="duplicated_categories",
                partition_by="id",
                order_by="updated_at desc",
            )
        }}
    )
