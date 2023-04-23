--
-- Providence
-- Pipelines
-- map_account DDL
--
create table if not exists {{ params.redshift_schema }}.{{ params.redshift_table }} (
  budget_account_id VARCHAR,
  vendor VARCHAR,
  vendor_id VARCHAR
)
