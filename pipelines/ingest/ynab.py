#
# Providence
# Data Pipelines
# Ingest YNAB Budget
#


from datetime import timedelta
from textwrap import dedent
from airflow.decorators import dag
from airflow.hooks.base import BaseHook
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from pendulum import datetime
from common import (
    AWS_CONNECTION_ID,
    DAG_ARGS,
    K8S_LABELS,
    SQL_DIR,
    get_aws_env,
    k8s_env_vars,
    DATASET_YNAB,
)


@dag(
    dag_id="pvd_ingest_ynab",
    schedule=timedelta(days=1),
    start_date=datetime(2023, 4, 4, tz="utc"),
    template_searchpath=[SQL_DIR],
    **DAG_ARGS,
)
def ingest_ynab_dag(
    rest_api_tag: str = "latest",
    ynab_budget_id: str = "f3f15316-e48c-4235-8d5d-1aa3191b3b8c",
    s3_bucket: str = "mrzzy-co-data-lake",
    redshift_external_schema: str = "lake",
    redshift_table: str = "source_ynab",
):
    dedent(
        f"""Ingests YNAB budget data into AWS Redshift.

    Parameters:
    - `s3_bucket`: Name of a existing S3 bucket to stage data.
    - `ynab_budget_id`: ID specifying the YNAB Budget to retrieve data for.
    - `rest_api_tag`: Tag specifying the version of the REST API Source container to use.
    - `redshift_external_schema`: External Schema that will contain the external
        table exposing the ingested data in Redshift.
    - `redshift_table`: Name of the External Table exposing the ingested data.

    Connections by expected id:
    - `pvd_ynab_src`:
        - `password`: YNAB API access token.
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
    Datasets:
    - Outputs `{DATASET_YNAB.uri}`.
    """
    )

    # Extract & load budget data with YNAB source into S3 as JSON
    ynab = BaseHook.get_connection("pvd_ynab_src")
    ingest_ynab = KubernetesPodOperator(
        task_id="ingest_ynab",
        # pool to limit load impact of concurrent requests on the YNAB API
        pool="ynab_api",
        image="ghcr.io/mrzzy/pvd-rest-api-src:{{ params.rest_api_tag }}",
        image_pull_policy="Always",
        labels=K8S_LABELS
        | {
            "app.kubernetes.io/name": "pvd-rest-api-src",
            "app.kubernetes.io/version": "{{ params.rest_api_tag }}",
        },
        arguments=[
            "GET",
            "https://api.ynab.com/v1/budgets/{{ params.ynab_budget_id }}",
            "s3://{{ params.s3_bucket }}/providence/grade=raw/source=ynab/date={{ ds }}/budget.json",
        ],
        env_vars=k8s_env_vars(
            {
                "REST_API_BEARER_TOKEN": ynab.password,
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
        sql="{% include 'source_ynab.sql' %}",
        autocommit=True,
        outlets=[DATASET_YNAB],
    )
    ingest_ynab >> drop_table >> create_table  # type: ignore


ingest_ynab_dag()
