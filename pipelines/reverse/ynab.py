#
# Providence
# Data Pipelines
# Reverse ETL YNAB Transactions
#

from datetime import timedelta
from textwrap import dedent
from airflow.datasets import Dataset
from airflow.decorators import dag
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)

from pendulum import datetime

from common import DAG_ARGS, DATASET_DBT, K8S_LABELS, YNAB_API_POOL, k8s_env_vars


@dag(
    dag_id="pvd_reverse_ynab",
    schedule=[Dataset(DATASET_DBT)],
    start_date=datetime(2023, 5, 10, tz="utc"),
    **DAG_ARGS,
)
def reverse_ynab(
    ynab_sink_tag: str = "latest",
    redshift_schema: str = "public",
    redshift_table: str = "mart_ynab_sink",
    ynab_budget_id: str = "f3f15316-e48c-4235-8d5d-1aa3191b3b8c",
    keep_k8s_pod: bool = False,
):
    dedent(
        f"""Reverse ETL writes transactions back to YNAB to account for Public Transport trips.

    Parameters:
    - `ynab_sink_tag`: Tag specifying the version of the YNAB Sink container to use.
    - `redshift_schema`: Schema containing the DBT mart table to source transactions from.
    - `redshift_table`: DBT Mart Table containing the transactions to write to YNAB.
    - `ynab_budget_id`: YNAB assigned Budget ID specifying the budget write transactions to.
    - `keep_k8s_pod`: Whether to leave K8s pods untouched after task completes.
        By default, the K8s pod created for the task will be cleaned up.

    Connections by expected id:
    - `ynab_api`:
        - `password`: YNAB API access token.
    - `redshift_default`:
        - `host`: Redshift DB endpoint.
        - `port`: Redshift DB port.
        - `login`: Redshift DB username.
        - `password`: Redshift DB password.
        - `schema`: Database to use by default.
        - `extra`:
            - `role_arn`: Instruct Redshift to assume this AWS IAM role when making AWS requests.

    Datasets:
    - Input `{DATASET_DBT}`
    """
    )
    KubernetesPodOperator(
        task_id="write_ynab",
        # pool to limit requests to YNAB API and reduce failures due to hitting the rate limit
        pool=YNAB_API_POOL,
        image="ghcr.io/mrzzy/pvd-ynab-sink:{{ params.ynab_sink_tag }}",
        image_pull_policy="Always",
        arguments=[
            "--begin={{ data_interval_start | ds }}",
            "--end={{ data_interval_end | ds }}",
            "{{ conn.redshift_default.host }}:{{ conn.redshift_default.port }}",
            # 'schema' in the redshift_default connection refers to database name
            "{{ conn.redshift_default.schema }}.{{ params.redshift_schema }}.{{ params.redshift_table }}",
            "{{ params.ynab_budget_id }}",
        ],
        labels=K8S_LABELS
        | {
            "app.kubernetes.io/name": "pvd-ynab-sink",
            "app.kubernetes.io/version": "{{ params.ynab_sink_tag }}",
        },
        env_vars=k8s_env_vars(
            {
                "AWS_REDSHIFT_USER": "{{ conn.redshift_default.login }}",
                "AWS_REDSHIFT_PASSWORD": "{{ conn.redshift_default.password }}",
                "YNAB_ACCESS_TOKEN": "{{ conn.ynab_api.password }}",
            }
        ),
        is_delete_operator_pod=keep_k8s_pod,
    )


reverse_ynab()
