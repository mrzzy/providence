#
# Providence
# Data Pipelines
# Common: Unit Tests
#

from typing import Dict
from unittest.mock import patch

from airflow.models import Connection

from common import get_rclone_env


def test_get_rclone_env(airflow_connections: Dict[str, Connection]):
    conn_id = "rclone_default"
    rclone = airflow_connections[conn_id]
    with patch.dict(
        "os.environ", {f"AIRFLOW_CONN_{conn_id.upper()}": rclone.get_uri()}
    ):
        remote_name = "default"
        prefix = f"RCLONE_CONFIG_{remote_name.upper()}"
        assert get_rclone_env(remote_name, conn_id) == {
            f"{prefix}_{key}": value for key, value in rclone.extra_dejson.items()
        }
