#
# Providence
# Data Pipelines
# Ingest SimplyGo
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
    dag_id="pvd_ingest_simplygo",
    schedule=timedelta(days=1),
    start_date=datetime(2023, 4, 4, tz="utc"),
)
def ingest_simplygo_dag(
    s3_bucket: str = "mrzzy-co-data-lake",
    simplygo_src_tag: str = "latest",
):
    """Ingests SimplyGo data into AWS Redshift, using AWS S3 as staging area.

    Parameters:
    - `s3_bucket`: Name of a existing S3 bucket to stage data.
    - `simplygo_src_tag`: Tag specifying the version of the SimplyGo Source container to use.

    Connections by expected id:
    - `pvd_simplygo_src`:
        - `login`: SimplyGo username.
        - `password`: SimplyGo password.
    - `aws_default`:
        - `login`: AWS Access Key ID.
        - `password`: AWS Access Secret Key.
        - `extras`:
            - `region`: AWS region.
    """
    # Extract & load SimplyGo data with SimplyGo source into S3 as JSON
    simplygo = BaseHook.get_connection("pvd_simplygo_src")
    ingest_simplygo = KubernetesPodOperator(
        task_id="ingest_simplygo",
        # pool to limit load impact of concurrent requests on the SimplyGo Website
        pool="simplygo_web",
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
            "{{ ds }}",
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


ingest_simplygo_dag()
