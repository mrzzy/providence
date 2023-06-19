#
# Providence
# Data Pipelines
# Common: Unit Tests
#

from typing import Dict
from unittest.mock import patch

from airflow.models import Connection

from common import rclone_conn_str


def test_rclone_conn_str(airflow_connections: Dict[str, Connection]):
    conn_id = "rclone_default"
    rclone = airflow_connections[conn_id]
    with patch.dict(
        "os.environ", {f"AIRFLOW_CONN_{conn_id.upper()}": rclone.get_uri()}
    ):
        assert rclone_conn_str(conn_id) == ":remote,key='value',key2='value2':"
