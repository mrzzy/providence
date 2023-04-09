#
# Providence
# Data Pipelines
# Data Ingestion
#

from os import path
from datetime import timedelta
from typing import Any, Dict, List
from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from pendulum import datetime
from kubernetes.client import models as k8s

from common import AWS_CONNECTION_ID, K8S_LABELS, get_aws_env, k8s_env_vars


@dag(
    dag_id="pvd_ingest_data",
    schedule=timedelta(days=1),
    start_date=datetime(2023, 2, 1, tz="utc"),
    catchup=False,
)
def ingest_dag(
    s3_bucket: str = "mrzzy-co-data-lake",
    simplygo_src_tag: str = "latest",
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
    # Extract & load SimplyGo data with SimplyGo source into S3 as JSON
    simplygo = BaseHook.get_connection("pvd_simplygo_src")
    ingest_simplygo = KubernetesPodOperator(
        task_id="ingest_simplygo",
        image="ghcr.io/mrzzy/pvd-simplygo-src:{{ params.simplygo_src_tag }}",
        image_pull_policy="Always",
        labels=K8S_LABELS
        | {
            "app.kubernetes.io/name": "simplygo_src",
            "app.kubernetes.io/component": "source",
            "app.kubernetes.io/version": "{{ params.simplygo_src_tag }}",
        },
        arguments=[
            "--trips-from",
            "{{  ds }}",
            "--trips-to",
            "{{ ds }}",
            "--output",
            "s3://{{ params.s3_bucket }}/providence/grade=raw/source=simplygo/date={{ ds }}/simplygo.json",
        ],
        env_vars=k8s_env_vars(
            {
                "SIMPLYGO_SRC_USERNAME": simplygo.login,
                "SIMPLYGO_SRC_PASSWORD": simplygo.password,
            }
            | get_aws_env(AWS_CONNECTION_ID)
        ),
    )

    # Extract & load budget data with YNAB source into S3 as JSON
    ynab = BaseHook.get_connection("pvd_ynab_src")
    ingest_ynab = KubernetesPodOperator(
        task_id="ingest_ynab",
        image="ghcr.io/mrzzy/pvd-ynab-src:{{ params.ynab_src_tag }}",
        image_pull_policy="Always",
        labels=K8S_LABELS
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
            | get_aws_env(AWS_CONNECTION_ID)
        ),
    )


ingest_dag()
