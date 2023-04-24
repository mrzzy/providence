#
# Providence
# Data Pipelines
# Ingest YNAB Budget
#


from datetime import timedelta
from airflow.decorators import dag
from airflow.hooks.base import BaseHook
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from pendulum import datetime
from common import AWS_CONNECTION_ID, K8S_LABELS, SQL_DIR, get_aws_env, k8s_env_vars


@dag(
    dag_id="pvd_ingest_ynab",
    schedule=timedelta(days=1),
    start_date=datetime(2023, 4, 4, tz="utc"),
    template_searchpath=[SQL_DIR],
)
def ingest_ynab_dag(
    ynab_src_tag: str = "latest",
    ynab_budget_id: str = "f3f15316-e48c-4235-8d5d-1aa3191b3b8c",
    s3_bucket: str = "mrzzy-co-data-lake",
    redshift_external_schema: str = "lake",
    redshift_table: str = "source_ynab",
):
    """Ingests YNAB budget data into AWS Redshift.

    Parameters:
    - `s3_bucket`: Name of a existing S3 bucket to stage data.
    - `ynab_budget_id`: ID specifying the YNAB Budget to retrieve data for.
    - `ynab_src_tag`: Tag specifying the version of the YNAB Source container to use.
    - `redshift_external_schema`: External Schema that will contain the external
        table exposing the ingested data in Redshift.
    - `redshift_table`: Name of the External Table exposing the ingested data.

    Connections by expected id:
    - `pvd_ynab_src`:
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

    # Extract & load budget data with YNAB source into S3 as JSON
    ynab = BaseHook.get_connection("pvd_ynab_src")
    ingest_ynab = KubernetesPodOperator(
        task_id="ingest_ynab",
        # pool to limit load impact of concurrent requests on the YNAB API
        pool="ynab_api",
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
        is_delete_operator_pod=False,
        log_events_on_failure=True,
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
        sql="{% include 'source_ynab.sql' %}",
        autocommit=True,
    )
    ingest_ynab >> drop_table >> create_table  # type: ignore


ingest_ynab_dag()
