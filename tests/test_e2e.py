#
# Providence
# End to End Tests
#

import os
import json
import stat

import pytest
from testcontainers.compose import DockerCompose

INGEST_DAG_ID = "pvd_ingest_data"


def test_ingest_dag():
    """End to End Test Providence Data Pipeline by performing 1 DAG run.

    Expects the following test environment:
    - docker-compose: to run Airflow in docker.
    - existing S3 bucket to be provided via the 'AWS_S3_TEST_BUCKET' env var.
    - access to a Kubernetes cluster configured via a kube config file provided
        by the 'KUBECONFIG' env var.
    """
    # admend permissions of KUBECONFIG to make sure containerized Airflow can read
    os.chmod(os.environ["KUBECONFIG"], stat.S_IROTH)
    # run standalone airflow with docker compose
    with DockerCompose("..", "docker-compose.yaml") as c:
        c.wait_for("http://localhost:8080")
        stdin, stdout, status = c.exec_in_container(
            "airflow",
            [
                "airflow",
                "dags",
                "test",
                INGEST_DAG_ID,
                "-c",
                json.dumps({"s3_bucket": os.environ["AWS_S3_TEST_BUCKET"]}),
            ],
        )
        if status != 0:
            raise AssertionError(
                f"Test Run of {INGEST_DAG_ID} DAG failed with nonzero status:\n"
                + stdout
            )
