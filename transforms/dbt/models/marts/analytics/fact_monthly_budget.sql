--
-- Providence
-- Transforms
-- DBT Analytics: Monthly budget Facts
--

-- grain 1 row: 1 monthly budget snapshot
select
    {{ dbt_utils.generate_surrogate_key(["c.budget_month", "b.id", "c.id"]) }} as "id",
    c.budget_month as month_date_id,
    b.id as budget_id,
    c.id as category_id,
    c.budget_amount as amount,
    c.goal_type as goal_type,
    c.goal_amount as goal_amount,
    c.goal_due as goal_due,
    c.updated_at as updated_at
from {{ ref("dim_budget_category") }} c
    inner join {{ ref("dim_budget") }} b on b.id = c.budget_id
