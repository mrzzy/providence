--
-- Providence
-- Transforms
-- DBT Intermediate: Unique Enriched Bank Statement
--
with
    keyed_statement as (
        select
            {{
                dbt_utils.generate_surrogate_key(
                    ["account_no", "transacted_on", "description"]
                )
            }} as "id", *
        from {{ ref("stg_uob_statement") }}
    ),

    unique_statement as (
        (
            {{
                deduplicate(
                    relation="keyed_statement",
                    partition_by="id",
                    order_by="processed_on desc",
                )
            }}
        )
    )

-- enrich statement with account dimension
select t.*, a.id as account_id
from unique_statement as t
left join {{ ref("dim_account") }} as a on a.vendor_id = t.account_no
