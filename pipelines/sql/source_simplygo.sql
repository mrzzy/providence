--
-- Providence
-- Pipelines
-- SimplyGo External Table DDL
--
CREATE EXTERNAL TABLE {{ params.redshift_external_schema }}.{{ params.redshift_table }} (
  scraped_on varchar,
  cards array<struct<id:varchar,name:varchar>>,
  trips_from varchar,
  trips_to varchar,
  trips array<struct<posting_ref:varchar,traveled_on:varchar,legs:array<struct<begin_at:varchar,cost_sgd:varchar,source:varchar,destination:varchar,mode:varchar>>,card_id:varchar>>
    ) PARTITIONED BY (date varchar) ROW
FORMAT
    SERDE 'org.openx.data.jsonserde.JsonSerDe'
    STORED AS TEXTFILE
      LOCATION 's3://{{ params.s3_bucket }}/providence/grade=raw/source=simplygo/'
