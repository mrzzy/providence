--
-- Providence
-- Transforms
-- DBT Analytics: Budget Category dimension
--
with
    unique_categories as (
        select
            {{
                dbt_utils.star(
                    ref("stg_ynab_budget_category"),
                    except=["id", "scraped_on"],
                )
            }},
            id as category_id,
            scraped_on as updated_at
        from
            (
                {{
                    dbt_utils.deduplicate(
                        relation=ref("stg_ynab_budget_category"),
                        partition_by="id",
                        order_by="scraped_on desc",
                    )
                }}
            )
    )

select
    {{ dbt_utils.generate_surrogate_key(["c.category_id", "c.budget_month"]) }} as "id",
    c.*,
    g.name as category_group
from unique_categories as c
inner join
    {{ ref("stg_ynab_budget_category_group") }} as g on g.id = c.category_group_id
