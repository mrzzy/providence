#
# Providence
# Data Pipelines
# Ingest UOB Export
#


from datetime import timedelta
from typing import Any, Dict
from textwrap import dedent
from airflow.datasets import Dataset
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
    get_aws_env,
    k8s_env_vars,
    DATASET_UOB,
)


@dag(
    dag_id="pvd_ingest_uob",
    schedule=timedelta(days=1),
    start_date=datetime(2023, 4, 2, 13, 0, tz="utc"),
    **DAG_ARGS,
)
def ingest_uob_dag(
    s3_bucket: str = "mrzzy-co-data-lake",
    export_prefix="providence/manual/uob/ACC_TXN_History_",
    pandas_etl_tag: str = "latest",
    keep_k8s_pod: bool = False,
):
    dedent(
        f"""Ingests manual UOB transaction export into AWS S3

    Parameters:
    - `s3_bucket`: Name of a existing S3 bucket to that contains the UOB export to ingest.
            The bucket will also be used to store ingested data.
    - `export_prefix` Path prefix under which UOB export is manually stored in the bucket.
    - `pandas_etl_tag`: Tag specifying the version of the Pandas ETL container to use.
    - `keep_k8s_pod`: Whether to leave K8s pods untouched after task completes.
        By default, the K8s pod created for the task will be cleaned up.

    Connections by expected id:
    - `aws_default`:
        - `login`: AWS Access Key ID.
        - `password`: AWS Access Secret Key.
        - `extras`:
            - `region`: AWS region.

    Datasets:
    - Outputs `{DATASET_UOB}`.
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
    KubernetesPodOperator.partial(
        task_id="convert_uob_pq",
        image="ghcr.io/mrzzy/pvd-pandas-etl-tfm:{{ params.pandas_etl_tag }}",
        image_pull_policy="Always",
        labels=K8S_LABELS
        | {
            "app.kubernetes.io/name": "pvd-pandas-etl-tfm",
            "app.kubernetes.io/version": "{{ params.pandas_etl_tag }}",
        },
        env_vars=k8s_env_vars(get_aws_env(AWS_CONNECTION_ID)),
        outlets=[Dataset(DATASET_UOB)],
        is_delete_operator_pod=keep_k8s_pod,
    ).expand(arguments=build_convert_args())


ingest_uob_dag()
