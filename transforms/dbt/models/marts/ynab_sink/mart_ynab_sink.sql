--
-- Providence
-- Transforms
-- DBT Marts: YNAB Sink
--
-- public transport trips yet to be accounted for.
select
    t.account_id,
    t.travel_date_id as "date",
    t.updated_at,
    -- ynab expresses amounts in milliunits: $1 = 1000 milliunits
    cast(- t.cost_sgd * 1000 as int) as amount,
    -- SG Gov: Land Transport Authority
    '0b849f31-3e30-4a00-8b49-053a8365133f' as payee_id,
    -- Public Transport budget category
    '8efad1f9-ef85-45e4-a85e-74f0207dc2c1' as category_id,
    'uncleared' as cleared,
    false as approved,
    null as flag_color,
    '0b849f31-3e30-4a00-8b49-053a8365133f' as split_payee_id,
    t.billing_ref as split_memo,
    -- group trips billed together in the same split_id under the same split
    -- transaction
    'pvd' || t.id as import_id,
    t.source || ' -> ' || t.destination as memo,
    -- warning: do not change, as it will break the left join below
    'public_transport:' || t.billing_ref as split_id
from {{ ref("fact_public_transport_trip_leg") }} as t
left join {{ ref("fact_accounting_transaction") }} as a on a.description = t.billing_ref
where t.is_billed and a.id is null
