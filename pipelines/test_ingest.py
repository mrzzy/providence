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

DAGS_DIR = Path(os.path.dirname(__file__))

INGEST_DAG_ID = "pvd_ingest_data"


def test_ingest_dag_import():
    # mock connections expected by DAGs
    connections = [
        Connection(
            conn_id="aws_default",
            conn_type="aws",
            login="test",
            password="test",
            extra={
                "region_name": "test",
            },
        ),
        Connection(
            conn_id="pvd_simplygo_src",
            conn_type="generic",
            login="test",
            password="test",
        ),
        Connection(
            conn_id="pvd_ynab_src",
            conn_type="generic",
            password="test",
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
