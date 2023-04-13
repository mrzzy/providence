#
# Providence
# End to End Tests
#

from datetime import datetime
import os
import json
from pathlib import Path
import stat
import boto3

import pytest
from testcontainers.compose import DockerCompose

DAG_IDS = ["pvd_ingest_simplygo", "pvd_ingest_ynab", "pvd_ingest_uob"]
RESOURCE_DIR = Path(".") / "resources"


@pytest.fixture
def s3_bucket():
    test_bucket = os.environ["AWS_S3_TEST_BUCKET"]

    # upload test uob export into test bucket
    s3 = boto3.client("s3")
    # dag finds uob exports by date so we include today's date in the s3 key
    key = datetime.utcnow().date.strftime(
        "providence/manual/uob/ACC_TXN_History_%d%m%Ytest.xls"
    )
    s3.upload_file(str(RESOURCE_DIR / "ACC_TXN_test.xls"), test_bucket, key)

    yield test_bucket

    # clean up test uob export
    s3.delete_object(Bucket=test_bucket, Key=key)


def test_ingest_dag(s3_bucket: str):
    """End to End Test Providence Data Pipeline by performing 1 DAG run.

    Expects the following test environment:
    - docker-compose: to run Airflow in docker.
    - existing S3 bucket to be provided via the 'AWS_S3_TEST_BUCKET' env var.
    - AWS credentials exposed via environment variables:
        - AWS_DEFAULT_REGION: AWS Region.
        - AWS_ACCESS_KEY_ID": AWS Access Key.
        - AWS_SECRET_ACCESS_KEY": Secret of AWS Access Key.
    - SimplyGo credentials: SIMPLYGO_SRC_USERNAME & SIMPLYGO_SRC_PASSWORD
    - YNAB credentials: YNAB_SRC_ACCESS_TOKEN
    - access to a Kubernetes cluster configured via a kube config file provided
        by the 'KUBECONFIG' env var.
    """
    # admend permissions of KUBECONFIG to make sure containerized Airflow can read
    os.chmod(os.environ["KUBECONFIG"], stat.S_IROTH)
    # run standalone airflow with docker compose
    with DockerCompose("..", "docker-compose.yaml") as c:
        c.wait_for("http://localhost:8080")
        for dag_id in DAG_IDS:
            stdin, stdout, status = c.exec_in_container(
                "airflow",
                [
                    "airflow",
                    "dags",
                    "test",
                    dag_id,
                    "-c",
                    json.dumps({"s3_bucket": s3_bucket}),
                ],
            )
            if status != 0:
                raise AssertionError(
                    f"Test Run of {dag_id} DAG failed with nonzero status:\n" + stdout
                )
