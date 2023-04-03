#
# Providence
# Data Pipelines
# Data Ingestion
#

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
from unittest import mock
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import os
from airflow.models import Connection, DagBag
from testcontainers.compose import DockerCompose

DAGS_DIR = Path(os.path.dirname(__file__))

INGEST_DAG_ID = "ingest_providence_data"


@pytest.mark.unit
def test_ingest_dag_import():
    # mock connections expected by DAGs
    connections = [
        Connection(
            conn_id="aws_default",
            conn_type="aws",
        ),
        Connection(
            conn_id="providence_simplygo_src",
            conn_type="generic",
        ),
    ]
    with mock.patch.dict(
        "os.environ",
        **{f"AIRFLOW_CONN_{c.conn_id.upper()}": c.get_uri() for c in connections},  # type: ignore
    ):
        dagbag = DagBag(DAGS_DIR)
    assert dagbag.import_errors == {}
    expected_dags = [INGEST_DAG_ID]
    for dag_id in expected_dags:
        assert dagbag.get_dag(dag_id) is not None


@pytest.mark.integration
def test_ingest_dag():
    """Integration Test Providence Data Pipeline by performing 1 DAG run.

    Expects the following test environment:
    - docker-compose: to run Airflow in docker.
    - existing S3 bucket to be provided via the 'AWS_S3_TEST_BUCKET' env var.
    - access to a Kubernetes cluster configured via a kube config file provided
        by the 'KUBECONFIG' env var.
    """
    # run standalone airflow with docker compose
    with DockerCompose(".", "docker-compose.yaml") as c:
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
