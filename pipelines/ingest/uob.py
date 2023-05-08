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
from pendulum.date import Date
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
    REDSHIFT_POOL,
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

    # Find a manual UOB exports to import to build convert_uob_pq task args
    @task
    def build_convert_args(
        params: Dict[str, Any] = None,  # type: ignore
        ds: str = None,  # type: ignore
        data_interval_start: DateTime = None,  # type: ignore
        data_interval_end: DateTime = None,  # type: ignore
    ):
        s3 = S3Hook()
        # assume that s3 objects modified between the data interval are new
        # exports to be imported
        export_keys = s3.list_keys(
            bucket_name=params["s3_bucket"],
            prefix=params["export_prefix"],
            from_datetime=data_interval_start,
            to_datetime=data_interval_end,
        )
        # build convert_uob_pq's pandas-etl transform args
        return [
            [
                "extract_uob",
                f"s3://{params['s3_bucket']}/{key}",
                f"s3://{params['s3_bucket']}/providence/grade=raw/source=uob/date={ds}/export.pq",
            ]
            for key in export_keys
        ]

    # Convert UOB transaction export to Parquet
    convert_uob_pq = KubernetesPodOperator.partial(
        task_id="convert_uob_pq",
        image="ghcr.io/mrzzy/pvd-pandas-etl-tfm:{{ params.pandas_etl_tag }}",
        image_pull_policy="Always",
        labels=K8S_LABELS
        | {
            "app.kubernetes.io/name": "pvd-pandas-etl-tfm",
            "app.kubernetes.io/version": "{{ params.pandas_etl_tag }}",
        },
        env_vars=k8s_env_vars(get_aws_env(AWS_CONNECTION_ID)),
    ).expand(arguments=build_convert_args())

    # expose ingested data via redshift external table
    drop_table = SQLExecuteQueryOperator(
        task_id="drop_table",
        conn_id="redshift_default",
        sql="DROP TABLE IF EXISTS {{ params.redshift_external_schema }}.{{ params.redshift_table }}",
        autocommit=True,
        pool=REDSHIFT_POOL,
    )

    create_table = SQLExecuteQueryOperator(
        task_id="create_table",
        conn_id="redshift_default",
        sql="{% include 'source_uob.sql' %}",
        autocommit=True,
        outlets=[DATASET_UOB],
        pool=REDSHIFT_POOL,
    )
    convert_uob_pq >> drop_table >> create_table  # type: ignore


ingest_uob_dag()
