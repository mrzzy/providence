#
# Providence
# Data Pipelines
# Pipelines: Unit  Tests
#

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, Iterable

import pytest
from unittest import mock
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import os
from airflow.models import Connection, DagBag

DAGS_DIR = Path(__file__).parent
DAG_IDS = [
    "pvd_schema",
    "pvd_ingest_account_map",
    "pvd_ingest_bank_card_map",
    "pvd_ingest_simplygo",
    "pvd_ingest_ynab",
    "pvd_ingest_uob",
    "pvd_transform_dbt",
    "pvd_reverse_ynab",
]


def test_ingest_dag_import(airflow_connections: Dict[str, Connection]):
    # mock connections expected by DAGs
    with mock.patch.dict(
        "os.environ",
        PYTHON_PATH=str(DAGS_DIR),
        # disable loading of example dags
        AIRFLOW__CORE__LOAD_EXAMPLES="False",
        **{
            f"AIRFLOW_CONN_{conn_id.upper()}": conn
            for conn_id, conn in airflow_connections.items()
        },
    ):
        dagbag = DagBag(DAGS_DIR)
    assert dagbag.import_errors == {}
    for dag_id in DAG_IDS:
        assert dagbag.get_dag(dag_id) is not None
