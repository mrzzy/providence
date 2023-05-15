#
# Providence
# Data Pipelines
# Ingest Manual Mappings
#
from textwrap import dedent
from airflow.datasets import Dataset

from pendulum import datetime
from airflow.decorators import dag
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.configuration import conf

from common import (
    DAG_ARGS,
    DATASET_MAP_ACCOUNT,
    DATASET_MAP_BANK_CARD,
    K8S_LABELS,
    REDSHIFT_POOL,
    SQL_DIR,
    k8s_env_vars,
)


def ingest_mapping_dag(
    out_dataset: str,
):
    def build_dag(
        mapping_path: str,
        redshift_table: str,
        create_table_sql: str,
        redshift_schema: str = "public",
        s3_bucket: str = "mrzzy-co-data-lake",
    ):
        dedent(
            f"""Ingest manually uploaded Mapping CSV to AWS Redshift.

        Parameters:
        - `mapping_path`: Path to the Mapping CSV on the bucket to ingest.
        - `redshift_table`: Name of the Redshift table to populate with mapping.
        - `create_table_sql`: SQL DDL Jinja template used to create Redshift table.
        - `out_dataset`: Dataset representing the mapping table that this DAG will create.
        - `redshift_schema`: Schema that will contain the mapping table.
        - `s3_bucket`: Name of a existing S3 bucket to that contains the mapping to ingest.

        Connections by expected id:
        - `redshift_default`:
            - `host`: Redshift DB endpoint.
            - `port`: Redshift DB port.
            - `login`: Redshift DB username.
            - `password`: Redshift DB password.
            - `schema`: Database to use by default.
            - `extra`:
                - `role_arn`: Instruct Redshift to assume this AWS IAM role when making AWS requests.

        Datasets:
        - Outputs to `{out_dataset}`.
        """
        )
        begin = SQLExecuteQueryOperator(
            task_id="begin",
            conn_id="redshift_default",
            sql="BEGIN",
            pool=REDSHIFT_POOL,
        )

        drop_table = SQLExecuteQueryOperator(
            task_id="drop_table",
            conn_id="redshift_default",
            sql="DROP TABLE IF EXISTS {{ params.redshift_schema }}.{{ params.redshift_table }}",
            pool=REDSHIFT_POOL,
        )

        create_table = SQLExecuteQueryOperator(
            task_id="create_table",
            conn_id="redshift_default",
            sql="{% include params.create_table_sql %}",
            pool=REDSHIFT_POOL,
        )

        copy_s3_table = S3ToRedshiftOperator(
            task_id="copy_s3_table",
            s3_bucket="{{ params.s3_bucket }}",
            s3_key="{{ params.mapping_path }}",
            schema="{{ params.redshift_schema }}",
            table="{{ params.redshift_table }}",
            copy_options=["FORMAT CSV", "IGNOREHEADER 1"],
            pool=REDSHIFT_POOL,
        )

        commit = SQLExecuteQueryOperator(
            task_id="commit",
            conn_id="redshift_default",
            sql="COMMIT",
            pool=REDSHIFT_POOL,
            outlets=[Dataset(out_dataset)],
        )

        begin >> drop_table >> create_table >> copy_s3_table >> commit  # type: ignore

    return build_dag


# dag to ingest mapping between YNAB budget account & Vendor account
dag(
    dag_id="pvd_ingest_account_map",
    start_date=datetime(2023, 4, 18),
    template_searchpath=[SQL_DIR],
    schedule="@once",
    **DAG_ARGS,
)(ingest_mapping_dag(out_dataset=DATASET_MAP_ACCOUNT))(
    redshift_table="map_account",
    create_table_sql="map_account.sql",
    mapping_path="providence/manual/mapping/account.csv",
)

# dag to ingest mapping between Bank card & Vendor Bank account
dag(
    dag_id="pvd_ingest_bank_card_map",
    start_date=datetime(2023, 5, 2),
    template_searchpath=[SQL_DIR],
    schedule="@once",
    **DAG_ARGS,
)(ingest_mapping_dag(out_dataset=DATASET_MAP_BANK_CARD))(
    redshift_table="map_bank_card",
    create_table_sql="map_bank_card.sql",
    mapping_path="providence/manual/mapping/bank_card.csv",
)
