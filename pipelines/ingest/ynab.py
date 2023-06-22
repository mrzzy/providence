#
# Providence
# Data Pipelines
# Ingest YNAB Budget
#


from datetime import timedelta
from textwrap import dedent
from airflow.datasets import Dataset
from airflow.decorators import dag
from airflow.hooks.base import BaseHook
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from pendulum import datetime
from common import (
    AWS_CONNECTION_ID,
    DAG_ARGS,
    K8S_LABELS,
    RCLONE_CONNECTION_ID,
    YNAB_API_POOL,
    get_aws_env,
    get_rclone_env,
    k8s_env_vars,
    DATASET_YNAB,
)


@dag(
    dag_id="pvd_ingest_ynab",
    schedule=timedelta(days=1),
    start_date=datetime(2023, 4, 4, tz="utc"),
    # TODO(mrzzy): remove default_args
    **(DAG_ARGS | {"default_args": {}}),
)
def ingest_ynab_dag(
    rest_api_tag: str = "latest",
    ynab_budget_id: str = "f3f15316-e48c-4235-8d5d-1aa3191b3b8c",
    bucket: str = "mrzzy-co-data-lake",
    keep_k8s_pod: bool = False,
):
    dedent(
        f"""Ingests YNAB budget data into a cloud storage bucket.

    Parameters:
    - `bucket`: Name of a existing cloud storage bucket to ingest data.
    - `ynab_budget_id`: ID specifying the YNAB Budget to retrieve data for.
    - `rest_api_tag`: Tag specifying the version of the REST API Source container to use.
    - `keep_k8s_pod`: Whether to leave K8s pods untouched after task completes.
        By default, the K8s pod created for the task will be cleaned up.

    Connections by expected id:
    - `ynab_api`:
        - `password`: YNAB API access token.
    - `rclone_default`:
        - `extra`: rclone remote config parameters
            See https://rclone.org/docs/#configure for provider specific config keys.

    Datasets:
    - Outputs `{DATASET_YNAB}`.
    """
    )

    # Extract & load YNAB budget data with REST API source
    rclone_remote = "default"
    KubernetesPodOperator(
        task_id="ingest_ynab",
        # pool to limit requests to YNAB API and reduce failures due to hitting the rate limit
        pool=YNAB_API_POOL,
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
            rclone_remote
            + ":{{ params.bucket }}/providence/grade=raw/source=ynab/date={{ ds }}/budget.json",
        ],
        env_vars=k8s_env_vars(
            {
                "REST_API_BEARER_TOKEN": "{{ conn.ynab_api.password }}",
            }
            | get_rclone_env(remote_name=rclone_remote, conn_id=RCLONE_CONNECTION_ID)
        ),
        outlets=[Dataset(DATASET_YNAB)],
        is_delete_operator_pod=keep_k8s_pod,
    )


ingest_ynab_dag()
