#
# Providence
# Integration Tests
# Pytest Fixtures

# Usage: Set the following environment variables:
# - B2_ACCOUNT_ID: B2 account id.
# - B2_APP_KEY: B2 application key credentials
# - PVD_LAKE_BUCKET: Name of the B2 bucket to use as data lake.
# - YNAB_BUDGET_ID: Id of the budget to 

import os
from datetime import date

import pytest
from prefect import flow
from prefect.blocks.system import Secret
from prefect.testing.utilities import prefect_test_harness
from prefect_aws import AwsClientParameters, AwsCredentials, S3Bucket

from simplygo import ingest_simplygo
from ynab import ingest_ynab


@pytest.fixture(scope="session")
def prefect():
    with prefect_test_harness():
        # setup credential blocks
        S3Bucket(
            bucket_name=os.environ["PVD_LAKE_BUCKET"],
            credentials=AwsCredentials(
                aws_access_key_id=os.environ["B2_ACCOUNT_ID"],
                aws_secret_access_key=os.environ["B2_APP_KEY"],
                aws_client_parameters=AwsClientParameters(
                    endpoint_url="s3.us-west-004.backblazeb2.com",
                ),
            ),
        ).save("pvd-data-lake", overwrite=True)

        Secret(value=os.environ["SIMPLYGO_SRC_USERNAME"]).save(
            "simplygo-src-username", overwrite=True
        )
        Secret(value=os.environ["SIMPLYGO_SRC_PASSWORD"]).save(
            "simplygo-src-password", overwrite=True
        )
        Secret(value=os.environ["YNAB_ACCESS_TOKEN"]).save(
            "ynab-access-token", overwrite=True
        )

        yield


@pytest.mark.asyncio
async def test_ingest_simplygo(prefect):
    await ingest_simplygo(date(2024, 5, 1))


@pytest.mark.asyncio
async def test_ingest_ynab(prefect):
    await ingest_ynab(os.environ["YNAB_BUDGET_ID"])
