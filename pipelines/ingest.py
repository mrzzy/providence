#
# Providence
# Data Pipelines
# Data Ingestion
#

from os import path
from datetime import timedelta
from typing import Dict
from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from airflow.models.baseoperator import BaseOperator
from pendulum import datetime
from kubernetes.client import models as k8s


def ingest_simplygo(
    k8s_labels: Dict[str, str],
    # TODO(mrzzy): change to latest on merge
    image_tag: str = "main",
) -> BaseOperator:
    """Build Task to ingest data from SimplyGo source.
    Spawns a K8s pod with Simplygo Source container configured to write data into S3.

    Args:
        image_tag: SimplyGo source container image to use tag.
        k8s_labels: K8s labels to add to K8s Pod created by the Airflow task.
    """
    # Extract SimplyGo data with SimplyGo source & load into S3
    connection = BaseHook.get_connection("providence_simplygo_src")
    extract_load_s3 = KubernetesPodOperator(
        task_id="ingest_simplygo",
        image=f"ghcr.io/mrzzy/providence-simplygo-src:{image_tag}",
        # TODO(mrzzy): remove on merge
        image_pull_policy="Always",
        labels=k8s_labels
        | {
            "app.kubernetes.io/name": "simpygo_src",
            "app.kubernetes.io/component": "source",
            "app.kubernetes.io/version": image_tag,
        },
        arguments=[
            "--trips-from",
            "{{ data_interval_start | ds }}",
            "--trips-to",
            "{{ data_interval_end | ds }}",
            "--output",
            "s3://{{ context.params.s3_bucket }}/providence/raw/simplygo/date={{ ds }}/data.json",
        ],
        env_vars=[
            k8s.V1EnvVar("SIMPLYGO_SRC_USERNAME", connection.login),
            k8s.V1EnvVar("SIMPLYGO_SRC_PASSWORD", connection.password),
        ],
        # TODO(mrzzy): remove testing
        is_delete_operator_pod=False,
    )
    return extract_load_s3


@dag(
    dag_id="ingest_providence_data",
    schedule=timedelta(days=1),
    start_date=datetime(2023, 2, 1, tz="utc"),
    catchup=False,
)
def ingest_data(
    s3_staging_bucket: str = "mrzzy-co-data-lake",
):
    """Providence Ingestion Data Pipeline.
    Ingests data from Data Sources into AWS Redshift & uses AWS S3 as staging area.

    Parameters:
    - `s3_bucket`: Name of a existing S3 bucket to stage data.
    - `k8s_labels` Labels to attach to all K8s pods created by this DAG.

    Connections by expected id:
    - `providence_simplygo_src":
        - **Login** SimplyGo username.
        - **Password** SimplyGo password.
    - `aws_default`:
        - **Login** AWS Access Key ID.
        - **Password** AWS Access Secret Key.
    """
    k8s_labels = {
        "app.kubernetes.io/part-of": "providence",
        "app.kubernetes.io/managed-by": "airflow",
    }
    ingest_simplygo(k8s_labels)


ingest_data()
