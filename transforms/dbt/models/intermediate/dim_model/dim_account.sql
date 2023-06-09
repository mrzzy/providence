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
            on_budget as is_cash
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
    )

select
    b.*,
    m.vendor,
    m.vendor_id,
    v.name as vendor_type,
    greatest(b.scraped_on, v.processed_on) as updated_at
from unique_ynab_accounts as b
left join map_uob_account as m on m.budget_account_id = b.id
left join unique_uob_accounts as v on v.account_no = m.vendor_id
