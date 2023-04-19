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
from pendulum import datetime
from common import AWS_CONNECTION_ID, K8S_LABELS, get_aws_env, k8s_env_vars


@dag(
    dag_id="pvd_ingest_ynab",
    schedule=timedelta(days=1),
    start_date=datetime(2023, 4, 4, tz="utc"),
)
def ingest_ynab_dag(
    ynab_src_tag: str = "latest",
    ynab_budget_id: str = "f3f15316-e48c-4235-8d5d-1aa3191b3b8c",
    s3_bucket: str = "mrzzy-co-data-lake",
):
    """Ingests YNAB budget data into AWS Redshift.

    Parameters:
    - `s3_bucket`: Name of a existing S3 bucket to stage data.
    - `ynab_budget_id`: ID specifying the YNAB Budget to retrieve data for.
    - `ynab_src_tag`: Tag specifying the version of the YNAB Source container to use.

    Connections by expected id:
    - `pvd_ynab_src`:
        - `password`: SimplyGo password.
    - `aws_default`:
        - `login`: AWS Access Key ID.
        - `password`: AWS Access Secret Key.
        - `extra`:
            - `region`: AWS region.
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
    )


ingest_ynab_dag()
