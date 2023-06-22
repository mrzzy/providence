#
# Providence
# Data Pipelines
# Common: Unit Tests
#

from typing import Dict
from unittest.mock import patch

from airflow.models import Connection

from common import RCLONE_CONNECTION_ID, get_rclone_env


def test_get_rclone_env(airflow_connections: Dict[str, Connection]):
    rclone = airflow_connections[RCLONE_CONNECTION_ID]
    with patch.dict(
        "os.environ", {f"AIRFLOW_CONN_{RCLONE_CONNECTION_ID.upper()}": rclone.get_uri()}
    ):
        remote_name = "default"
        prefix = f"RCLONE_CONFIG_{remote_name.upper()}"
        assert get_rclone_env(remote_name, RCLONE_CONNECTION_ID) == {
            f"{prefix}_{key.upper()}": value
            for key, value in rclone.extra_dejson.items()
        }
