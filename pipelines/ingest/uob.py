#
# Providence
# Data Pipelines
# Ingest UOB Export
#


from datetime import timedelta
from typing import Any, Dict
from textwrap import dedent
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from pendulum import datetime
from kubernetes.client import models as k8s
from pendulum.datetime import DateTime
from airflow.decorators import task, dag
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)

from common import (
    AWS_CONNECTION_ID,
    DAG_ARGS,
    K8S_LABELS,
    SQL_DIR,
    get_aws_env,
    k8s_env_vars,
    DATASET_UOB,
)


@dag(
    dag_id="pvd_ingest_uob",
    schedule=timedelta(days=1),
    start_date=datetime(2023, 4, 2, 13, 0, tz="utc"),
    template_searchpath=[SQL_DIR],
    **DAG_ARGS,
)
def ingest_uob_dag(
    s3_bucket: str = "mrzzy-co-data-lake",
    export_prefix="providence/manual/uob/ACC_TXN_History_",
    pandas_etl_tag: str = "latest",
    redshift_external_schema: str = "lake",
    redshift_table: str = "source_uob",
):
    dedent(
        f"""Ingests manual UOB transaction export into AWS S3, exposing it as
    external Table in AWS Redshift.

    Parameters:
    - `s3_bucket`: Name of a existing S3 bucket to that contains the UOB export to ingest.
            The bucket is also used to stage data for load into Redshift.
    - `export_prefix` Path prefix under which UOB export is manually stored in the bucket.
    - `pandas_etl_tag`: Tag specifying the version of the Pandas ETL container to use.
    - `redshift_external_schema`: External Schema that will contain the external
        table exposing the ingested data in Redshift.
    - `redshift_table`: Name of the External Table exposing the ingested data.
    Connections by expected id:
    - `aws_default`:
        - `login`: AWS Access Key ID.
        - `password`: AWS Access Secret Key.
        - `extras`:
            - `region`: AWS region.
    - `redshift_default`:
        - `host`: Redshift DB endpoint.
        - `port`: Redshift DB port.
        - `login`: Redshift DB username.
        - `password`: Redshift DB password.
        - `schema`: Database to use by default.
        - `extra`:
            - `role_arn`: Instruct Redshift to assume this AWS IAM role when making AWS requests.
    Datasets:
    - Outputs `{DATASET_UOB.uri}`.
    """
    )

    # Find latest UOB export
    @task
    def find_uob_export(params: Dict[str, Any] = None, data_interval_end: DateTime = None):  # type: ignore
        s3 = S3Hook()
        export_keys = s3.list_keys(
            bucket_name=params["s3_bucket"],
            prefix=f"{params['export_prefix']}",
        )
        # exports are given a increasing numeric suffix, use max() to return the last one
        return f"s3://{params['s3_bucket']}/{max(export_keys)}"

    # Convert UOB transaction export to Parquet
    convert_uob_pq = KubernetesPodOperator(
        task_id="convert_uob_pq",
        image="ghcr.io/mrzzy/pvd-pandas-etl-tfm:{{ params.pandas_etl_tag }}",
        image_pull_policy="Always",
        labels=K8S_LABELS
        | {
            "app.kubernetes.io/name": "pandas-etl",
            "app.kubernetes.io/component": "transform",
            "app.kubernetes.io/version": "{{ params.pandas_etl_tag }}",
        },
        arguments=[
            "extract_uob",
            find_uob_export(),
            "s3://{{ params.s3_bucket }}/providence/grade=raw/source=uob/date={{ ds }}/export.pq",
        ],
        env_vars=k8s_env_vars(get_aws_env(AWS_CONNECTION_ID)),
        is_delete_operator_pod=False,
        log_events_on_failure=True,
    )

    # expose ingested data via redshift external table
    drop_table = SQLExecuteQueryOperator(
        task_id="drop_table",
        conn_id="redshift_default",
        sql="DROP TABLE IF EXISTS {{ params.redshift_external_schema }}.{{ params.redshift_table }}",
        autocommit=True,
    )

    create_table = SQLExecuteQueryOperator(
        task_id="create_table",
        conn_id="redshift_default",
        sql="{% include 'source_uob.sql' %}",
        autocommit=True,
        outlets=[DATASET_UOB],
    )
    convert_uob_pq >> drop_table >> create_table  # type: ignore


ingest_uob_dag()
