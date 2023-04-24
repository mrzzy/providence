#
# Providence
# Data Pipelines
# Common
#


from datetime import timedelta
from pathlib import Path
from typing import Dict, List

from airflow.hooks.base import BaseHook
from airflow.models import BaseOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from kubernetes.client import models as k8s

# common args passed to all dags
DAG_ARGS = {
    "tags": ["providence"],
    # common args passed to all tasks
    "default_args": {
        # retry with exponential backoff on task failure
        "retries": 3,
        "retry_delay": timedelta(minutes=3),
        "retry_exponential_backoff": True,
        # email notification on task failure
        "email": ["program.nom@gmail.com"],
        "email_on_failure": True,
        "tags": ["providence"],
    },
}
AWS_CONNECTION_ID = "aws_default"
K8S_LABELS = {
    "app.kubernetes.io/part-of": "providence",
    "app.kubernetes.io/managed-by": "airflow",
}
SQL_DIR = str(Path(__file__).parent / "sql")


def get_aws_env(conn_id: str) -> Dict[str, str]:
    """Get environment variables used to configure AWS access from the Airflow connection.

    Args:
        conn_id: ID of the Airflow connection to retrieve for aws credentials.
    Returns:
        Dict of environment variable name & value needed to configure AWS.
    """
    aws = BaseHook.get_connection(conn_id)
    return {
        "AWS_DEFAULT_REGION": aws.extra_dejson["region_name"],
        "AWS_ACCESS_KEY_ID": str(aws.login),
        "AWS_SECRET_ACCESS_KEY": aws.password,
    }


def k8s_env_vars(env_vars: Dict[str, str]) -> List[k8s.V1EnvVar]:
    """Convert given env_vars into list of K8s env vars."""
    return [k8s.V1EnvVar(name, value) for name, value in env_vars.items()]


def build_dbt_task(task_id: str, select: str) -> BaseOperator:
    """Construct a DBT Build Airflow Task.

    Args:
        task_id:
            Task ID to assign to the task.
        select:
            DBT selector specifying which models to build. See
            https://docs.getdbt.com/reference/node-selection/syntax.

    Params:
    - `redshift_external_schema`: Optional. External Schema that will contains the external
        tables exposing the ingested data in Redshift. Defaults to 'lake'.
    - `redshift_schema`: Schema that will contain DBT model tables.
    - `redshift_table`: Name of the External Table exposing the ingested data.
    - `dbt_tag`: Tag specifying the version of the DBT transform container to use.
    - `dbt_target`: Target DBT output profile to use for building DBT models.

    Connections by expected id:
    - `redshift_default`:
        - `login`: Redshift DB username.
        - `password`: Redshift DB password.
    """
    return KubernetesPodOperator(
        task_id=task_id,
        # guard with concurrency pool to prevent db conflicts with multiple dbt runs
        pool="dbt",
        image="ghcr.io/mrzzy/pvd-dbt-tfm:{{ params.dbt_tag }}",
        image_pull_policy="Always",
        arguments=[
            "build",
            "--select",
            select,
            "--vars",
            '{"schema": "{{ params.redshift_schema }}", "external_schema": "{{ params.redshift_external_schema }}"}',
        ],
        labels=K8S_LABELS
        | {
            "app.kubernetes.io/name": "dbt",
            "app.kubernetes.io/component": "transform",
            "app.kubernetes.io/version": "{{ params.dbt_tag }}",
        },
        env_vars=k8s_env_vars(
            {
                "AWS_REDSHIFT_USER": "{{ conn.redshift_default.login }}",
                "AWS_REDSHIFT_PASSWORD": "{{ conn.redshift_default.password }}",
                "DBT_TARGET": "{{ params.dbt_target }}",
            }
        ),
        is_delete_operator_pod=False,
        log_events_on_failure=True,
    )
