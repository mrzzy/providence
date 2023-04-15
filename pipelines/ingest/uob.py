#
# Providence
# Data Pipelines
# Ingest UOB Export
#


from datetime import timedelta
from typing import Any, Dict
from pendulum import datetime
from kubernetes.client import models as k8s
from pendulum.datetime import DateTime
from airflow.decorators import task, dag
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)

from common import AWS_CONNECTION_ID, K8S_LABELS, get_aws_env, k8s_env_vars


@dag(
    dag_id="pvd_ingest_uob",
    schedule=timedelta(weeks=1),
    # 1300hrs UTC -> 2300hrs in Asia/Singapore
    start_date=datetime(2023, 4, 9, 13, 0, tz="utc"),
)
def ingest_uob_dag(
    s3_bucket: str = "mrzzy-co-data-lake",
    export_prefix="providence/manual/uob/ACC_TXN_History_",
    pandas_etl_tag: str = "latest",
):
    """Ingests manual UOB transaction export into AWS Redshift.

    Parameters:
    - `s3_bucket`: Name of a existing S3 bucket to that contains the UOB export to ingest.
            The bucket is also used to stage data for load into Redshift.
    - `export_prefix` Path prefix under which UOB export is manually stored in the bucket.
    - `pandas_etl_tag`: Tag specifying the version of the Pandas ETL container to use.

    Connections by expected id:
    - `aws_default`:
        - `login`: AWS Access Key ID.
        - `password`: AWS Access Secret Key.
        - `extras`:
            - `region`: AWS region.
    """

    # Find UOB export for the dag data interval
    @task
    def find_uob_export(params: Dict[str, Any] = None, data_interval_end: DateTime = None):  # type: ignore
        s3 = S3Hook()
        export_keys = s3.list_keys(
            bucket_name=params["s3_bucket"],
            prefix=f"{params['export_prefix']}{data_interval_end.strftime('%d%m%Y')}",
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
    )


ingest_uob_dag()
