#
# Providence
# Pipelines
# Schema
#

from textwrap import dedent
from airflow.decorators import dag
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from pendulum import datetime

from common import DAG_ARGS, REDSHIFT_POOL, SQL_DIR


@dag(
    dag_id="pvd_schema",
    schedule=None,
    start_date=datetime(2023, 5, 15, tz="utc"),
    template_searchpath=[SQL_DIR],
)
def apply_schema(
    s3_bucket: str = "mrzzy-co-data-lake",
    glue_data_catalog: str = "data-lake",
    redshift_schema: str = "public",
    redshift_external_schema: str = "lake",
):
    dedent(
        """Applies schema & tables on AWS Redshift used as base for other DAGs.

        As this DAG will potentially cause data loss, it must be manually triggered.

        Parameters:
        - `glue_data_catalog` Name of the Glue Data Catalog to bind the External
            schema to. If the data catalog specified does not exist, it will be created.
        - `s3_bucket` Name of S3 bucket storing the actual data exposed by the External Tables.
        - `redshift_external_schema`: External Schema that will contain the external
            tables exposing the ingested data in Redshift.
        - `redshift_schema`: Schema that will contain the normal tables

        Connections by id:
         `redshift_default`:
            - `host`: Redshift DB endpoint.
            - `port`: Redshift DB port.
            - `login`: Redshift DB username.
            - `password`: Redshift DB password.
            - `schema`: Database to use by default.
            - `extra`:
                - `role_arn`: Instruct Redshift to assume this AWS IAM role when making AWS requests.
        """
    )
    # External Schema & Tables
    # replace external schemal
    drop_external_schema = SQLExecuteQueryOperator(
        task_id="drop_external_schema",
        conn_id="redshift_default",
        sql="DROP SCHEMA IF EXISTS {{ params.redshift_external_schema }}",
        autocommit=True,
        pool=REDSHIFT_POOL,
    )

    create_external_schema = SQLExecuteQueryOperator(
        task_id="create_external_schema",
        conn_id="redshift_default",
        sql="{% include 'external_schema.sql' %}",
        autocommit=True,
        pool=REDSHIFT_POOL,
    )
    drop_external_schema >> create_external_schema  # type: ignore

    # create external tables to expose external ingested data ingested by each data source
    for source in ["simplygo", "uob", "ynab"]:
        delete_table = SQLExecuteQueryOperator(
            task_id=f"delete_{source}_external_table",
            conn_id="redshift_default",
            sql=(
                "DROP TABLE IF EXISTS {{ params.redshift_external_schema }}.source_%s"
                % source
            ),
            autocommit=True,
            pool=REDSHIFT_POOL,
        )

        create_table = SQLExecuteQueryOperator(
            task_id=f"create_{source}_external_table",
            conn_id="redshift_default",
            sql="{% include 'source_" + source + ".sql' %}",
            autocommit=True,
            pool=REDSHIFT_POOL,
        )

        create_external_schema >> delete_table >> create_table  # type: ignore

    # Mapping Tables
    for mapping in ["account", "bank_card"]:
        drop_table = SQLExecuteQueryOperator(
            task_id=f"drop_map_{mapping}_table",
            conn_id="redshift_default",
            sql="DROP TABLE IF EXISTS {{ params.redshift_schema }}.map_%s" % mapping,
            pool=REDSHIFT_POOL,
        )

        create_table = SQLExecuteQueryOperator(
            task_id=f"create_map_{mapping}_table",
            conn_id="redshift_default",
            sql="{% include 'map_" + mapping + ".sql' %}",
            pool=REDSHIFT_POOL,
        )

        drop_table >> create_table  # type: ignore


apply_schema()
