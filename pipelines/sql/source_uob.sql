--
-- Providence
-- Pipelines
-- UOB External Table DDL
--
CREATE EXTERNAL TABLE {{ params.redshift_external_schema }}.{{ params.redshift_table }} (
  "transaction date" varchar,
  "transaction description" varchar,
  withdrawal double precision,
  deposit double precision,
  "available balance" double precision,
  "account number" varchar,
  "account type" varchar,
  "statement period" varchar,
  currency varchar,
  _pandas_etl_transformed_on varchar
)
ROW FORMAT
  SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
  STORED AS PARQUET
    LOCATION 's3://mrzzy-co-dev/providence/grade=raw/source=uob/'
