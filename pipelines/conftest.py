#
# Providence
# Data Pipelines
# Unit Test Config
#

from typing import Dict
import pytest
from airflow.models import Connection

from common import RCLONE_CONNECTION_ID


@pytest.fixture
def airflow_connections() -> Dict[str, Connection]:
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
            conn_id="ynab_api",
            conn_type="generic",
            password="test",
        ),
        Connection(
            conn_id=RCLONE_CONNECTION_ID,
            conn_type="generic",
            extra={
                "type": "remote",
                "key": "value",
                "key2": "value2",
            },
        ),
    ]
    return {c.conn_id: c for c in connections}  # type: ignore
