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
    YNAB_API_POOL,
    get_aws_env,
    k8s_env_vars,
    DATASET_YNAB,
)


@dag(
    dag_id="pvd_ingest_ynab",
    schedule=timedelta(days=1),
    start_date=datetime(2023, 4, 4, tz="utc"),
    **DAG_ARGS,
)
def ingest_ynab_dag(
    rest_api_tag: str = "latest",
    ynab_budget_id: str = "f3f15316-e48c-4235-8d5d-1aa3191b3b8c",
    s3_bucket: str = "mrzzy-co-data-lake",
):
    dedent(
        f"""Ingests YNAB budget data into AWS S3.

    Parameters:
    - `s3_bucket`: Name of a existing S3 bucket to store ingested data.
    - `ynab_budget_id`: ID specifying the YNAB Budget to retrieve data for.
    - `rest_api_tag`: Tag specifying the version of the REST API Source container to use.

    Connections by expected id:
    - `ynab_api`:
        - `password`: YNAB API access token.
    - `aws_default`:
        - `login`: AWS Access Key ID.
        - `password`: AWS Access Secret Key.
        - `extra`:
            - `region`: AWS region.

    Datasets:
    - Outputs `{DATASET_YNAB}`.
    """
    )

    # Extract & load budget data with YNAB source into S3 as JSON
    ingest_ynab = KubernetesPodOperator(
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
            "s3://{{ params.s3_bucket }}/providence/grade=raw/source=ynab/date={{ ds }}/budget.json",
        ],
        env_vars=k8s_env_vars(
            {
                "REST_API_BEARER_TOKEN": "{{ conn.ynab_api.password }}",
            }
            | get_aws_env(AWS_CONNECTION_ID)
        ),
        outlets=[Dataset(DATASET_YNAB)],
    )


ingest_ynab_dag()
