--
-- Providence
-- Transforms
-- DBT Staging: YNAB budget category
--
select
    cast(c.id as varchar) as id,
    cast(c.name as varchar) as "name",
    cast(s.id as varchar) as budget_id,
    cast(c.category_group_id as varchar) as category_group_id,
    -- ynab expresses amounts in milliunits: 1000 milliunits = $1
    cast(c.goal_target_month as date) as goal_due,
    cast(c.deleted as boolean) as is_deleted,
    cast(m.month as date) as budget_month,
    cast(s._ynab_src_scraped_on as timestamp) as scraped_on,
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
from {{ source("ynab", "source_ynab") }} as s, s.months as m, s.categories as c
