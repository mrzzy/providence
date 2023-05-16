#
# Providence
# Data Pipelines
# Ingest SimplyGo
#

from os import path
from datetime import timedelta
from textwrap import dedent
from typing import Any, Dict, List
from airflow.datasets import Dataset
from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from pendulum import datetime
from kubernetes.client import models as k8s

from common import (
    AWS_CONNECTION_ID,
    DAG_ARGS,
    K8S_LABELS,
    get_aws_env,
    k8s_env_vars,
    DATASET_SIMPLYGO,
)


@dag(
    dag_id="pvd_ingest_simplygo",
    schedule=timedelta(days=1),
    start_date=datetime(2023, 4, 4, tz="utc"),
    **DAG_ARGS,
)
def ingest_simplygo_dag(
    s3_bucket: str = "mrzzy-co-data-lake",
    simplygo_src_tag: str = "latest",
    keep_k8s_pod: bool = False,
):
    dedent(
        f"""Ingests SimplyGo data into AWS S3.

    Parameters:
    - `s3_bucket`: Name of a existing S3 bucket to ingest data.
    - `simplygo_src_tag`: Tag specifying the version of the SimplyGo Source container to use.
    - `keep_k8s_pod`: Whether to leave K8s pods untouched after task completes.
        By default, the K8s pod created for the task will be cleaned up.
    Connections by expected id:
    - `pvd_simplygo_src`:
        - `login`: SimplyGo username.
        - `password`: SimplyGo password.
    - `aws_default`:
        - `login`: AWS Access Key ID.
        - `password`: AWS Access Secret Key.
        - `extra`:
            - `region`: AWS region.

    Datasets:
    - Outputs `{DATASET_SIMPLYGO}`.
    """
    )
    # Extract & load SimplyGo data with SimplyGo source into S3 as JSON
    simplygo = BaseHook.get_connection("pvd_simplygo_src")
    ingest_simplygo = KubernetesPodOperator(
        task_id="ingest_simplygo",
        # pool to limit load impact of concurrent requests on the SimplyGo Website
        pool="simplygo_web",
        image="ghcr.io/mrzzy/pvd-simplygo-src:{{ params.simplygo_src_tag }}",
        image_pull_policy="Always",
        arguments=[
            # simplygo takes up to 5 days to clear & bill trips, scrape the last
            # 7 days worth of trips to ensure we capture trips when they are billed.
            "--trips-from",
            "{{ macros.ds_add(ds,-7) }}",
            "--trips-to",
            "{{ ds }}",
            "--output",
            "s3://{{ params.s3_bucket }}/providence/grade=raw/source=simplygo/date={{ ds }}/simplygo.json",
        ],
        labels=K8S_LABELS
        | {
            "app.kubernetes.io/name": "pvd-simplygo-src",
            "app.kubernetes.io/version": "{{ params.simplygo_src_tag }}",
        },
        env_vars=k8s_env_vars(
            {
                "SIMPLYGO_SRC_USERNAME": simplygo.login,
                "SIMPLYGO_SRC_PASSWORD": simplygo.password,
            }
            | get_aws_env(AWS_CONNECTION_ID)
        ),
        outlets=[Dataset(DATASET_SIMPLYGO)],
        is_delete_operator_pod=keep_k8s_pod,
    )


ingest_simplygo_dag()
