--
-- Providence
-- Transforms
-- DBT Marts: Finance Dashboard: CasCash Flow for Sankey Diagram
--
with
    statistics as (
        select
            year_month,
            sum(income) as total_income,
            abs(sum(spending)) as total_spending
        from {{ ref("mart_finance_dashboard") }}
        group by 1
    ),

    income_payees as (
        select
            year_month, payee_name as src, 'Income' as dest, sum(income) as amount
        from {{ ref("mart_finance_dashboard") }}
        group by 1, 2, 3
    ),

    spending_contributions as (
        -- income's contribution to spending
        select
            year_month,
            'Income' as src,
            'Spending' as dest,
            least(total_spending, total_income) as amount
        from statistics
        union all
        -- saving's contribution to spending
        select
            year_month,
            'Spent Savings' as src,
            'Spending' as dest,
            greatest(total_spending - total_income, 0) as amount
        from statistics
    ),

    income_savings as (
        -- income's contribution to savings
        select
            year_month,
            'Income' as src,
            'Savings' as amount,
            greatest(total_income - total_spending, 0) as amount
        from statistics
    ),

    spending_categories as (
        select
            year_month,
            'Spending' as src,
            budget_category as dest,
            abs(sum(spending)) as amount
        from {{ ref("mart_finance_dashboard") }}
        group by 1, 2, 3
    ),

    savings_categories as (
        -- savings used as investment capital
        select
            year_month,
            'Savings' as src,
            'Investment' as dest,
            -- only tabulate deductions (amount < 0) made for investment
            abs(sum(least(transaction_amount, 0))) as amount
        from {{ ref("mart_finance_dashboard") }}
        where
            -- Investment Capital group
            budget_category_group_id = '4b8aa46d-bed8-4dba-bee5-d438640d2d9d'
            and account_is_cash
            and transaction_is_transfer
        group by 1,2,3
        union all
        -- savings saved as cash
        select
            year_month,
            'Savings' as src,
            'Cash' as dest,
            sum(transaction_amount) as amount
        from {{ ref("mart_finance_dashboard") }}
        where account_is_cash
        group by 1,2,3
    )

-- compile src-dest columns for sankey diagram:
-- income payees \ spent savings \     /> savings-> savings categories
-- income payees -> income -> spending -> spending categories
select *
from
    (
        select *
        from income_payees
        union all
        select *
        from spending_contributions
        union all
        select *
        from income_savings
        union all
        select *
        from spending_categories
        union all
        select *
        from savings_categories
    )
where amount > 0
