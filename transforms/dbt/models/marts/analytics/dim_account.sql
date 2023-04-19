--
-- Providence
-- Transforms
-- DBT Analytics: Account Dimension
--
with
    -- enrich budget account with uob bank account info.
    map_uob_account as (
        select * from {{ ref("stg_map_budget_account") }} where vendor = 'UOB'
    ),

    uob_accounts as (
        select
            {% set except_cols = ["type", "on_budget", "scraped_on", "payee_id"] %}
            {{
                dbt_utils.star(
                    ref("stg_ynab_account"),
                    except=except_cols,
                    relation_alias="b",
                )
            }},
            b."type" as budget_type,
            b.on_budget as is_liquid,
            m.vendor,
            m.vendor_id,
            v.name as vendor_type,
            greatest(b.scraped_on, v.statement_end) as updated_at
        from map_uob_account as m
        inner join {{ ref("stg_ynab_account") }} as b on b.id = m.budget_account_id
        inner join {{ ref("stg_uob_account") }} as v on v.account_no = m.vendor_id
    ),

    unmapped_accounts as (
        -- derive rest of the budget accounts not mapped to a vendor accouns via
        -- anti-join
        select
            {{
                dbt_utils.star(
                    ref("stg_ynab_account"),
                    except=except_cols,
                    relation_alias="b",
                )
            }},
            b."type" as budget_type,
            b.on_budget as is_liquid,
            null as vendor,
            null as vendor_id,
            null as vendor_type,
            b.scraped_on as updated_at
        from {{ ref("stg_ynab_account") }} as b
        where
            not exists (
                select 1
                from {{ ref("stg_map_budget_account") }} as m
                where m.budget_account_id = b.id
            )
    ),

    all_accounts as (
        select *
        from uob_accounts
        union all
        select *
        from unmapped_accounts
    )

select *
from
    (
        -- deduplicate on id
        {{
            dbt_utils.deduplicate(
                relation="all_accounts",
                partition_by="id",
                order_by="updated_at desc",
            )
        }}
    )
