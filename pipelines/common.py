#
# Providence
# Data Pipelines
# Common
#


from datetime import timedelta
from pathlib import Path
from typing import Dict, List
from airflow.datasets import Dataset

from airflow.hooks.base import BaseHook
from airflow.models import BaseOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from kubernetes.client import models as k8s

AWS_CONNECTION_ID = "aws_default"
K8S_LABELS = {
    "app.kubernetes.io/part-of": "providence",
    "app.kubernetes.io/managed-by": "airflow",
    "app.kubernetes.io/component": "{{ dag.dag_id }}",
    "app.kubernetes.io/instance": "{{ task.task_id }}",
}
SQL_DIR = str(Path(__file__).parent / "sql")
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
# datasets for data-aware dag scheduling
DATASET_MAP_ACCOUNT = Dataset("redshift://map_account")
DATASET_SIMPLYGO = Dataset("redshift://simplygo")
DATASET_YNAB = Dataset("redshift://ynab")
DATASET_UOB = Dataset("redshift://uob")


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
