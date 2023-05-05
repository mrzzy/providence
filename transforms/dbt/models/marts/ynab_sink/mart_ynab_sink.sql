--
-- Providence
-- Transforms
-- DBT Marts: YNAB Sink
--
-- public transport trips yet to be accounted for.
select
    'ynab_sink:' || t.id as import_id,
    'public_transport:' || t.billing_ref as subtransaction_group_id,
    t.account_id,
    t.updated_at as "date",
    -- ynab expresses amounts in milliunits: 1000 milliunits = $1
    t.cost_sgd * 1000 as amount,
    '0b849f31-3e30-4a00-8b49-053a8365133f' as payee_id,
    -- SG Gov: Land Transport Authority
    '8efad1f9-ef85-45e4-a85e-74f0207dc2c1' as category_id,
    -- Public Transport budget category
    t.billing_ref as memo,
    'uncleared' as cleared,
    true as approved,
    null as flag_color
from {{ ref("fact_public_transport_trip_leg") }} as t
where
    t.is_billed
    and t.billing_ref
    not in (select distinct description from {{ ref("fact_accounting_transaction") }})
