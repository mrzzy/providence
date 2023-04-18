--
-- Providence
-- Transforms
-- DBT Analytics: Budget Category dimension
--

with flat_categories as  (
    select
        {{ dbt_utils.generate_surrogate_key(["c.id", "c.budget_month"]) }} as id,
        {{ dbt_utils.star(ref("stg_ynab_budget_category"), except=["id", "scraped_on"], relation_alias="c") }},
        c.id as ynab_id,
        c.scraped_on as updated_at,
        g.name as category_group
    from
        {{ ref("stg_ynab_budget_category") }} c
        inner join {{ ref("stg_ynab_budget_category_group") }} g on g.id = c.category_group_id
)
fd
select * from (
    {{
    dbt_utils.deduplicate(
        relation="flat_categories",
        partition_by="id",
        order_by="updated_at desc",
    )
    }}
)
