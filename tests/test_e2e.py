#
# Providence
# End to End Tests
#

from collections.abc import Iterator
import os
import json
import stat
import string
import boto3
import random
from pathlib import Path
from datetime import date, timedelta

import pytest
from testcontainers.compose import DockerCompose

DAG_IDS = [
    "pvd_ingest_simplygo",
    "pvd_ingest_ynab",
    "pvd_ingest_uob",
    "pvd_ingest_account_map",
]
RESOURCE_DIR = Path(__file__).parent / "resources"


def random_suffix(n=8) -> str:
    """Generate a random suffix of the given length"""
    return "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(n)
    )


@pytest.fixture
def e2e_suffix() -> str:
    suffix = random_suffix()
    print(f"random suffix for e2e test: {suffix}")
    return suffix


@pytest.fixture
def s3_bucket(e2e_suffix: str) -> Iterator[str]:
    # create test bucket for e2e test
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(f"mrzzy-co-providence-e2e-{e2e_suffix}")
    # by default buckets are created in us-east-1, use default region instead.
    bucket.create(
        CreateBucketConfiguration={
            "LocationConstraint": os.environ["AWS_DEFAULT_REGION"]
        },
    )

    # upload test uob export into test bucket
    # dag finds uob exports by end of data interval so we include today + day's date in the s3 key
    key = (date.today() + timedelta(days=7)).strftime(
        "providence/manual/uob/ACC_TXN_History_%d%m%Ytest.xls"
    )
    bucket.Object(key).upload_file(str(RESOURCE_DIR / "ACC_TXN_test.xls"))

    # copy account mapping from dev bucket to test bucket
    account_map_key = "providence/manual/mapping/account.csv"
    bucket.Object(account_map_key).copy_from(
        CopySource={"Bucket": "mrzzy-co-dev", "Key": account_map_key}
    )

    yield bucket.name

    # clean up test bucket
    bucket.objects.delete()
    bucket.delete()


@pytest.fixture
def redshift_schema(e2e_suffix: str) -> Iterator[str]:
    # create redshift schema within 'dev' database for e2e test
    redshift = boto3.client("redshift-data")
    e2e_schema = f"providence_e2e_{e2e_suffix}"
    db_params = {
        "WorkgroupName": "main",
        "Database": "dev",
    }
    redshift.batch_execute_statement(
        Sqls=[f"CREATE SCHEMA {e2e_schema}"],
        **db_params,
    )

    yield e2e_schema

    # clean up test schema
    redshift.batch_execute_statement(
        Sqls=[f"DROP SCHEMA {e2e_schema}"],
        **db_params,
    )


def test_ingest_dag(s3_bucket: str, redshift_schema: str):
    """End to End Test Providence Data Pipeline by performing 1 DAG run.

    Expects the following test environment:
    - docker-compose: to run Airflow in docker.
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
                    json.dumps(
                        {
                            "s3_bucket": s3_bucket,
                            "redshift_schema": redshift_schema,
                        }
                    ),
                ],
            )
            if status != 0:
                raise AssertionError(
                    f"Test Run of {dag_id} DAG failed with nonzero status:\n" + stdout
                )
