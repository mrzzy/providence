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
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from pendulum import datetime
from kubernetes.client import models as k8s

from common import (
    AWS_CONNECTION_ID,
    K8S_LABELS,
    SQL_DIR,
    build_dbt_task,
    get_aws_env,
    k8s_env_vars,
)


@dag(
    dag_id="pvd_ingest_simplygo",
    schedule=timedelta(days=1),
    start_date=datetime(2023, 4, 4, tz="utc"),
    template_searchpath=[SQL_DIR],
)
def ingest_simplygo_dag(
    s3_bucket: str = "mrzzy-co-data-lake",
    simplygo_src_tag: str = "latest",
    redshift_external_schema: str = "lake",
    redshift_table: str = "source_simplygo",
    dbt_tag: str = "latest",
    dbt_target: str = "prod",
):
    """Ingests SimplyGo data into AWS S3, exposing it as external table in Redshift.

    Refreshes DBT models that depend on the SimplyGo data.

    Parameters:
    - `s3_bucket`: Name of a existing S3 bucket to stage data.
    - `simplygo_src_tag`: Tag specifying the version of the SimplyGo Source container to use.
    - `redshift_external_schema`: External Schema that will contains the external
        table exposing the ingested data in Redshift.
    - `redshift_table`: Name of the External Table exposing the ingested data.
    - `dbt_tag`: Tag specifying the version of the DBT transform container to use.
    - `dbt_target`: Target DBT output profile to use for building DBT models.
    Connections by expected id:
    - `pvd_simplygo_src`:
        - `login`: SimplyGo username.
        - `password`: SimplyGo password.
    - `aws_default`:
        - `login`: AWS Access Key ID.
        - `password`: AWS Access Secret Key.
        - `extra`:
            - `region`: AWS region.
    - `redshift_default`:
        - `host`: Redshift DB endpoint.
        - `port`: Redshift DB port.
        - `login`: Redshift DB username.
        - `password`: Redshift DB password.
        - `schema`: Database to use by default.
        - `extra`:
            - `role_arn`: Instruct Redshift to assume this AWS IAM role when making AWS requests.
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

    # expose ingest data via redshift external table
    drop_table = SQLExecuteQueryOperator(
        task_id="drop_table",
        conn_id="redshift_default",
        sql="DROP TABLE IF EXISTS {{ params.redshift_external_schema }}.{{ params.redshift_table }}",
        autocommit=True,
    )

    create_table = SQLExecuteQueryOperator(
        task_id="create_table",
        conn_id="redshift_default",
        sql="{% include 'source_simplygo.sql' %}",
        autocommit=True,
    )

    # rebuild all dbt models that depend on ingested mapping
    build_dbt = build_dbt_task(task_id="build_dbt", select="source:simplygo+")
    ingest_simplygo >> drop_table >> create_table >> build_dbt  # type: ignore


ingest_simplygo_dag()
