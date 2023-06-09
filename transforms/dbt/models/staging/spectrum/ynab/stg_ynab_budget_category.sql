--
-- Providence
-- Transforms
-- DBT Staging: YNAB budget category
--
select
    cast(c.id as varchar) as "id",
    cast(c.name as varchar) as "name",
    cast(s.data.budget.id as varchar) as budget_id,
    cast(c.category_group_id as varchar) as category_group_id,
    -- ynab expresses amounts in milliunits: 1000 milliunits = $1
    cast(c.goal_target_month as date) as goal_due,
    cast(c.deleted as boolean) as is_deleted,
    cast(m.month as date) as budget_month,
    coalesce(
        cast(s._rest_api_src_scraped_on as timestamp), {{ timestamp_min() }}
    ) as scraped_on,
    cast(c.budgeted as decimal(13, 2)) / 1000 as budget_amount,
    case
        cast(c.goal_type as varchar)
        when 'TB'
        then 'Target Category Balance'
        when 'TBD'
        then 'Target Category Balance by Date'
        when 'MF'
        then 'Monthly Funding'
        when 'NEED'
        then 'Plan Your Spending'
    end as goal_type,
    cast(c.goal_target as decimal(13, 2)) / 1000 as goal_amount
from
    {{ source("ynab", "source_ynab") }} as s,
    s.data.budget.months as m,
    m.categories as c
