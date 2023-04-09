#
# Providence
# Data Pipelines
# Utilities
#


from typing import Dict, List

from airflow.hooks.base import BaseHook
from kubernetes.client import models as k8s


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
