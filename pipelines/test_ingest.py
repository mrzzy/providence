#
# Providence
# Data Pipelines
# Data Ingestion
#

from os.path import dirname
import pytest
from unittest import mock
from airflow.models import Connection, DagBag

DAGS_DIR = dirname(__file__)


@pytest.mark.unit
def test_ingest_providence_data_import():
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
    expected_dags = ["ingest_providence_data"]
    for dag_id in expected_dags:
        assert dagbag.get_dag(dag_id) is not None
