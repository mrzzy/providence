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


@dag(
    dag_id="ingest_providence_data",
    schedule=timedelta(days=1),
    start_date=datetime(2023, 2, 1, tz="utc"),
    catchup=False,
)
def ingest_data(s3_bucket: str = "mrzzy-co-data-lake", simplygo_src_tag: str = "main"):
    """Providence Ingestion Data Pipeline.
        Ingests data from Data Sources into AWS Redshift & uses AWS S3 as staging area.
    fa
        Parameters:
        - `s3_bucket`: Name of a existing S3 bucket to stage data.
        - `simplygo_src_tag`: Tag specifying the version of the SimplyGo source container to use.

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
    # Extract SimplyGo data with SimplyGo source & load into S3
    simplygo_connection = BaseHook.get_connection("providence_simplygo_src")
    extract_load_s3 = KubernetesPodOperator(
        task_id="ingest_simplygo",
        image="ghcr.io/mrzzy/providence-simplygo-src:{{ params.simplygo_src_tag }}",
        # TODO(mrzzy): remove on merge
        image_pull_policy="always",
        labels=k8s_labels
        | {
            "app.kubernetes.io/name": "simpygo_src",
            "app.kubernetes.io/component": "source",
            "app.kubernetes.io/version": "{{ params.simplygo_src_tag }}",
        },
        # TODO: mount s3
        volume_mounts=[
            k8s.V1VolumeMount(
                name="s3-bucket",
                mount_path="/mnt/s3",
            )
        ],
        arguments=[
            "--trips-from",
            "{{ data_interval_start | ds }}",
            "--trips-to",
            "{{ data_interval_end | ds }}",
            "--output",
            "/mnt/s3/providence/raw/simplygo/date={{ ds }}/data.json",
        ],
        env_vars=[
            k8s.V1EnvVar("SIMPLYGO_SRC_USERNAME", simplygo_connection.login),
            k8s.V1EnvVar("SIMPLYGO_SRC_PASSWORD", simplygo_connection.password),
        ],
        # TODO(mrzzy): remove testing
        is_delete_operator_pod=False,
    )


ingest_data()
