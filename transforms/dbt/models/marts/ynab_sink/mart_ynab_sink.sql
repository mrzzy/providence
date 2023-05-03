--
-- Providence
-- Transforms
-- DBT Marts: YNAB Sink
--
-- public transport trips yet to be accounted for.
select
    t.account_id,
    t.updated_at as "date",
    t.cost_sgd as amount,
    '0b849f31-3e30-4a00-8b49-053a8365133f' as payee_id,
    -- SG Gov: Land Transport Authority
    '8efad1f9-ef85-45e4-a85e-74f0207dc2c1' as category_id,
    -- Public Transport budget category
    t.billing_ref as memo,
    'uncleared' as cleared,
    true as approved,
    null as flag_color,
    null as import_id,
    'public_transport_' || t.billing_ref as subtransaction_group_id
from {{ ref("fact_public_transport_trip_leg") }} as t
where
    t.is_billed
    and t.billing_ref
    not in (select distinct description from {{ ref("fact_accounting_transaction") }})
