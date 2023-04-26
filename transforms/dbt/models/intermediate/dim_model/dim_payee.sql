--
-- Providence
-- Transforms
-- DBT Intermediate: Payee Dimension
--

with unique_payees as  (
    {{
        deduplicate(
            relation=ref("stg_ynab_payee"),
            partition_by="id",
            order_by="scraped_on desc",
        )
    }}
)
select
    {{ dbt_utils.star(ref("stg_ynab_payee"), except=["scraped_on"], relation_alias="p") }},
    scraped_on as updated_at,
    coalesce(f.is_unaccounted, false) as is_unaccounted,
    coalesce(f.is_passive, false) as is_passive
from unique_payees p
left join {{ ref("ynab_payee_flag") }} f on f.payee_id = p.id
