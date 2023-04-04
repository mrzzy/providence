#
# Providence
# Data Pipelines
# Data Ingestion
#

from os import path
from datetime import timedelta
from typing import Dict, List
from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from airflow.models.baseoperator import BaseOperator
from pendulum import datetime
from kubernetes.client import models as k8s


def get_aws_env(conn_id: str) -> Dict[str, str]:
    """Get environment variables used to configure AWS access from the Airflow connection.

    Args:
        conn_id: ID of the Airflow connection to retrieve for aws credentials.
    Returns:
        Dict of environment variable name & value needed to configure AWS.
    """
    aws = BaseHook.get_connection(conn_id)
    return {
        "AWS_DEFAULT_REGION": aws.extra_dejson["region_name"],
        "AWS_ACCESS_KEY_ID": str(aws.login),
        "AWS_SECRET_ACCESS_KEY": aws.password,
    }


def k8s_env_vars(env_vars: Dict[str, str]) -> List[k8s.V1EnvVar]:
    """Convert given env_vars into list of K8s env vars."""
    return [k8s.V1EnvVar(name, value) for name, value in env_vars.items()]


@dag(
    dag_id="ingest_providence_data",
    schedule=timedelta(days=1),
    start_date=datetime(2023, 2, 1, tz="utc"),
    catchup=False,
)
def ingest_dag(
    s3_bucket: str = "mrzzy-co-data-lake",
    simplygo_src_tag: str = "main",
):
    """Providence Ingestion Data Pipeline.
    Ingests data from Data Sources into AWS Redshift & uses AWS S3 as staging area.

    Parameters:
    - `s3_bucket`: Name of a existing S3 bucket to stage data.
    - `simplygo_src_tag`: Tag specifying the version of the SimplyGo source container to use.

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
    load_simplygo_s3 = KubernetesPodOperator(
        task_id="ingest_simplygo",
        image="ghcr.io/mrzzy/providence-simplygo-src:{{ params.simplygo_src_tag }}",
        image_pull_policy="Always",
        labels=k8s_labels
        | {
            "app.kubernetes.io/name": "simpygo_src",
            "app.kubernetes.io/component": "source",
            "app.kubernetes.io/version": "{{ params.simplygo_src_tag }}",
        },
        arguments=[
            "--trips-from",
            "{{ data_interval_start | ds }}",
            "--trips-to",
            "{{ data_interval_end | ds }}",
            "--output",
            "s3://{{ params.s3_bucket }}/providence/raw/simplygo/{{ ds }}.json",
        ],
        env_vars=k8s_env_vars(
            {
                "SIMPLYGO_SRC_USERNAME": simplygo_connection.login,
                "SIMPLYGO_SRC_PASSWORD": simplygo_connection.password,
            }
            | get_aws_env("aws_default")
        ),
    )


ingest_dag()
