--
-- Providence
-- Transforms
-- DBT Intermediate: Monthly Budget Fact table
--
-- grain 1 row: 1 monthly budget snapshot
select
    "id",
    budget_month as month_date_id,
    budget_id,
    "id" as category_id,
    budget_amount as amount,
    updated_at
from {{ ref("int_unique_budget_category") }}
