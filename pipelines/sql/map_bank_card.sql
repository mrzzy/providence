--
-- Providence
-- Pipelines
-- map_bank_card DDL
--
CREATE TABLE IF NOT EXISTS {{ params.redshift_schema }}.map_bank_card (
  bank_card_id VARCHAR,
  vendor VARCHAR,
  vendor_id VARCHAR
)
