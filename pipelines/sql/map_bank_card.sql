--
-- Providence
-- Pipelines
-- map_bank_card DDL
--
create table if not exists {{ params.redshift_schema }}.{{ params.redshift_table }} (
  bank_card_id VARCHAR,
  vendor VARCHAR,
  vendor_id VARCHAR
)
