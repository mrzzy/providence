--
-- Providence
-- Pipelines
-- External Schema DDL
--
CREATE EXTERNAL SCHEMA IF NOT EXISTS lake
FROM data catalog
    database '{{ params.glue_data_catalog }}'
    iam_role '{{ conn.redshift_default.extra_dejson.role_arn }}'
CREATE EXTERNAL DATABASE IF NOT EXISTS
