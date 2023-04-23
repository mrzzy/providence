--
-- Providence
-- Pipelines
-- UOB External Table DDL
--
CREATE EXTERNAL TABLE {{ params.redshift_external_schema }}.{{ params.redshift_table }} (
  "transaction date" varchar,
  "transaction description" varchar,
  withdrawal decimal(10, 2),
  deposit decimal(10, 2),
  "available balance" decimal(10, 2),
  "account number" varchar,
  "account type" varchar,
  "statement period" varchar,
  currency varchar,
  _pandas_etl_transformed_on varchar
) PARTITIONED BY (date varchar) ROW
FORMAT
  SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
  STORED AS PARQUET
    LOCATION 's3://mrzzy-co-dev/providence/grade=raw/source=uob/'
