--
-- Providence
-- Transforms
-- DBT Intermediate: Account Dimension
--
with
    -- deduplicate ynab & uob account rows
    unique_ynab_accounts as (
        select
            {{
                dbt_utils.star(
                    ref("stg_ynab_account"),
                    except=["type", "on_budget", "payee_id"],
                )
            }},
            "type" as budget_type,
            on_budget as is_liquid
        from
            (
                {{
                    deduplicate(
                        relation=ref("stg_ynab_account"),
                        partition_by="id",
                        order_by="scraped_on desc",
                    )
                }}
            )
    ),

    unique_uob_accounts as (
        select account_no, "name", processed_on
        from
            (
                {{
                    deduplicate(
                        relation=ref("stg_uob_statement"),
                        partition_by="account_no",
                        order_by="processed_on desc",
                    )
                }}
            )
    ),

    -- enrich budget account with uob bank account info.
    map_uob_account as (
        select * from {{ ref("stg_map_budget_account") }} where vendor = 'UOB'
    ),

    merged_uob_accounts as (
        select
            b.*,
            m.vendor,
            m.vendor_id,
            v.name as vendor_type,
            greatest(b.scraped_on, v.processed_on) as updated_at
        from map_uob_account as m
        inner join unique_ynab_accounts as b on b.id = m.budget_account_id
        inner join unique_uob_accounts as v on v.account_no = m.vendor_id
    ),

    unmapped_accounts as (
        -- derive rest of the budget accounts not mapped to a vendor accounts
        -- via anti-join
        select
            b.*,
            null as vendor,
            null as vendor_id,
            null as vendor_type,
            b.scraped_on as updated_at
        from unique_ynab_accounts as b
        where
            not exists (
                select 1
                from {{ ref("stg_map_budget_account") }} as m
                where m.budget_account_id = b.id
            )
    )

select *
from merged_uob_accounts
union all
select *
from unmapped_accounts
