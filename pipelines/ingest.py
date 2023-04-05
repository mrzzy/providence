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
    dag_id="pvd_ingest_data",
    schedule=timedelta(days=1),
    start_date=datetime(2023, 2, 1, tz="utc"),
    catchup=False,
)
def ingest_dag(
    s3_bucket: str = "mrzzy-co-data-lake",
    simplygo_src_tag: str = "main",
    ynab_src_tag: str = "latest",
    ynab_budget_id: str = "f3f15316-e48c-4235-8d5d-1aa3191b3b8c",
):
    """Providence Ingestion Data Pipeline.
    Ingests data from Data Sources into AWS Redshift & uses AWS S3 as staging area.

    Parameters:
    - `s3_bucket`: Name of a existing S3 bucket to stage data.
    - `simplygo_src_tag`: Tag specifying the version of the SimplyGo Source container to use.
    - `ynab_src_tag`: Tag specifying the version of the YNAB Source container to use.
    - `ynab_budget_id`: ID specifying the YNAB Budget to retrieve data for.

    Connections by expected id:
    - `pvd_simplygo_src":
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
    # Extract & load SimplyGo data with SimplyGo source into S3
    simplygo = BaseHook.get_connection("pvd_simplygo_src")
    load_simplygo_s3 = KubernetesPodOperator(
        task_id="ingest_simplygo",
        image="ghcr.io/mrzzy/pvd-simplygo-src:{{ params.simplygo_src_tag }}",
        image_pull_policy="Always",
        labels=k8s_labels
        | {
            "app.kubernetes.io/name": "simplygo_src",
            "app.kubernetes.io/component": "source",
            "app.kubernetes.io/version": "{{ params.simplygo_src_tag }}",
        },
        arguments=[
            "--trips-from",
            "{{ data_interval_start | ds }}",
            "--trips-to",
            "{{ data_interval_end | ds }}",
            "--output",
            "s3://{{ params.s3_bucket }}/providence/grade=raw/source=simplygo/date={{ ds }}/simplygo.json",
        ],
        env_vars=k8s_env_vars(
            {
                "SIMPLYGO_SRC_USERNAME": simplygo.login,
                "SIMPLYGO_SRC_PASSWORD": simplygo.password,
            }
            | get_aws_env("aws_default")
        ),
    )

    # Extract & load budget data with YNAB source into S3
    ynab = BaseHook.get_connection("pvd_ynab_src")
    load_ynab_s3 = KubernetesPodOperator(
        task_id="ingest_ynab",
        image="ghcr.io/mrzzy/pvd-ynab-src:{{ params.ynab_src_tag }}",
        image_pull_policy="Always",
        labels=k8s_labels
        | {
            "app.kubernetes.io/name": "ynab",
            "app.kubernetes.io/component": "source",
            "app.kubernetes.io/version": "{{ params.ynab_src_tag }}",
        },
        arguments=[
            "{{ params.ynab_budget_id }}",
            "s3://{{ params.s3_bucket }}/providence/grade=raw/source=ynab/date={{ ds }}/budget.json",
        ],
        env_vars=k8s_env_vars(
            {
                "YNAB_SRC_ACCESS_TOKEN": ynab.password,
            }
            | get_aws_env("aws_default")
        ),
    )


ingest_dag()
