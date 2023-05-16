# Providence
# Data Pipelines
# DBT Transform
#

from textwrap import dedent
from airflow.datasets import Dataset
from airflow.decorators import dag
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from pendulum import datetime

from common import (
    DAG_ARGS,
    DATASET_DBT,
    DATASET_MAP_ACCOUNT,
    DATASET_MAP_BANK_CARD,
    DATASET_SIMPLYGO,
    DATASET_YNAB,
    DATASET_UOB,
    K8S_LABELS,
    k8s_env_vars,
)


@dag(
    dag_id="pvd_transform_dbt",
    schedule=[
        Dataset(DATASET_SIMPLYGO),
        Dataset(DATASET_YNAB),
        Dataset(DATASET_UOB),
    ],
    start_date=datetime(2023, 4, 24, tz="utc"),
    **DAG_ARGS,
)
def transform_dbt(
    dbt_tag: str = "latest",
    dbt_target: str = "prod",
    dbt_select: str = "*",
    redshift_schema: str = "public",
    redshift_external_schema: str = "lake",
    keep_k8s_pod: bool = False,
):
    dedent(
        f"""Transform raw data tables into DBT models on AWS Redshift.

    Parameters:
    - `dbt_tag`: Tag specifying the version of the DBT transform container to use.
    - `dbt_target`: Target DBT output profile to use for building DBT models.
    - `dbt_select`: [DBT selector](https://docs.getdbt.com/reference/node-selection/syntax)
            specifying which models to build.
    - `redshift_schema`: Schema that will contain the mapping table & DBT tables.
    - `redshift_external_schema`: External Schema that will contains the external
        tables exposing the ingested data in Redshift.
    - `keep_k8s_pod`: Whether to leave K8s pods untouched after task completes.
        By default, the K8s pod created for the task will be cleaned up.

    Connections by expected id:
    - `redshift_default`: `login`: Redshift DB username.
        - `password`: Redshift DB password.

    Datasets:
    - Input `{DATASET_SIMPLYGO}`
    - Input `{DATASET_YNAB}`
    - Input `{DATASET_UOB}`
    Outputs:
    - Output `{DATASET_DBT}`
    """
    )
    KubernetesPodOperator(
        task_id="transform_dbt",
        # guard with concurrency pool to prevent db conflicts with multiple dbt runs
        pool="dbt",
        image="ghcr.io/mrzzy/pvd-dbt-tfm:{{ params.dbt_tag }}",
        image_pull_policy="Always",
        arguments=[
            "build",
            "--select",
            dbt_select,
            "--vars",
            '{"schema": "{{ params.redshift_schema }}", "external_schema": "{{ params.redshift_external_schema }}"}',
        ],
        labels=K8S_LABELS
        | {
            "app.kubernetes.io/name": "pvd-dbt-tfm",
            "app.kubernetes.io/version": "{{ params.dbt_tag }}",
        },
        env_vars=k8s_env_vars(
            {
                "AWS_REDSHIFT_USER": "{{ conn.redshift_default.login }}",
                "AWS_REDSHIFT_PASSWORD": "{{ conn.redshift_default.password }}",
                # airflow connections uses 'schema' to store selected database
                "AWS_REDSHIFT_DB": "{{ conn.redshift_default.schema }}",
                "DBT_TARGET": "{{ params.dbt_target }}",
            }
        ),
        outlets=[Dataset(DATASET_DBT)],
        is_delete_operator_pod=keep_k8s_pod,
    )


transform_dbt()
