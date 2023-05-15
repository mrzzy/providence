--
-- Providence
-- Pipelines
-- map_account DDL
--
CREATE TABLE IF NOT EXISTS {{ params.redshift_schema }}.map_account (
  budget_account_id VARCHAR,
  vendor VARCHAR,
  vendor_id VARCHAR
)
