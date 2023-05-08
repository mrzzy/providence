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
    "pvd_ingest_account_map",
    "pvd_ingest_simplygo",
    "pvd_ingest_ynab",
    "pvd_ingest_uob",
    "pvd_transform_dbt",
]


def random_suffix(n=8) -> str:
    """Generate a random suffix of the given length"""
    return "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(n)
    )


@pytest.fixture
def e2e_suffix() -> str:
    suffix = random_suffix()
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

    # copy test data to test bucket
    # DAG locates export by mod time, not the date in the numeric suffix
    uob_export_key = "providence/manual/uob/ACC_TXN_History_09042023114932.xls"
    bucket.Object(uob_export_key).copy_from(
        CopySource={"Bucket": "mrzzy-co-data-lake", "Key": uob_export_key},
    )
    account_map_key = "providence/manual/mapping/account.csv"
    bucket.Object(account_map_key).copy_from(
        CopySource={"Bucket": "mrzzy-co-data-lake", "Key": account_map_key},
    )

    yield bucket.name

    # clean up test bucket
    bucket.objects.delete()
    bucket.delete()


@pytest.fixture
def redshift_db(e2e_suffix: str):
    # create redshift database for e2e test
    redshift = boto3.client("redshift-data")
    e2e_db = f"providence_e2e_{e2e_suffix}"
    redshift.execute_statement(
        Sql=f"CREATE DATABASE {e2e_db}",
        # use 'dev' database to bootstrap create db statement
        Database="dev",
        WorkgroupName="main",
    )
    yield e2e_db

    # clean up e2e test db
    redshift.execute_statement(
        Sql=f"DROP DATABASE {e2e_db}",
        Database="dev",
        WorkgroupName="main",
    )


@pytest.fixture
def redshift_external_schema(e2e_suffix: str, redshift_db: str) -> str:
    redshift = boto3.client("redshift-data")
    e2e_schema = f"providence_e2e_lake_{e2e_suffix}"

    # create test external schema backed by test glue data catalog
    redshift.execute_statement(
        Sql=f"""
        CREATE EXTERNAL SCHEMA IF NOT EXISTS lake
        FROM DATA CATALOG
            DATABASE '{e2e_schema}'
            IAM_ROLE 'arn:aws:iam::132307318913:role/warehouse'
            CREATE EXTERNAL DATABASE IF NOT EXISTS
        """,
        Database=redshift_db,
        WorkgroupName="main",
    )

    return "lake"


def test_ingest_dag(s3_bucket: str, redshift_db: str, redshift_external_schema: str):
    """End to End Test Providence Data Pipelines by performing 1 DAG run.

    Expects the following test environment:
    - docker-compose: to run Airflow in docker.
    - AWS credentials exposed via environment variables:
        - AWS_DEFAULT_REGION: AWS Region.
        - AWS_ACCESS_KEY_ID": AWS Access Key.
        - AWS_SECRET_ACCESS_KEY": Secret of AWS Access Key.
    - AWS Redshift:
        - AWS_REDSHIFT_USER: Redshift username.
        - AWS_REDSHIFT_PASSWORD: Redshift password.
        - AWS_REDSHIFT_DB: Redshift database to use.
    - SimplyGo credentials: SIMPLYGO_SRC_USERNAME & SIMPLYGO_SRC_PASSWORD
    - YNAB credentials: YNAB_ACCESS_TOKEN
    - access to a Kubernetes cluster configured via a kube config file provided
        by the 'KUBECONFIG' env var.
    """
    # admend permissions of KUBECONFIG to make sure containerized Airflow can read
    os.chmod(os.environ["KUBECONFIG"], stat.S_IROTH)
    # pass dedicated redshift db via env var to docker-compose
    os.environ["AWS_REDSHIFT_DB"] = redshift_db
    # run standalone airflow with docker compose
    with DockerCompose("..", "docker-compose.yaml") as c:
        c.wait_for("http://localhost:8080")

        # import concurrency pools to reduce e2e failures caused by concurrency
        stdin, stdout, status = c.exec_in_container(
            "airflow",
            ["airflow", "pools", "import", "/opt/airflow/dags/concurrency_pools.json"],
        )
        if status != 0:
            raise AssertionError(
                f"Could not import concurrency pools from JSON:\n{stdout}"
            )

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
                            "redshift_external_schema": redshift_external_schema,
                            "dbt_target": "dev",
                        }
                    ),
                ],
            )
            if status != 0:
                raise AssertionError(
                    f"Test Run of {dag_id} DAG failed with nonzero status:\n" + stdout
                )
