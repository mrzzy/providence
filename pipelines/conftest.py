#
# Providence
# Integration Tests
# Pytest Fixtures

# Usage: Set the following environment variables:
# - B2_ACCOUNT_ID: B2 account id.
# - B2_APP_KEY: B2 application key credentials
# - PVD_LAKE_BUCKET: Name of the B2 bucket to use as data lake.


import os
import pytest
from prefect.testing.utilities import prefect_test_harness
from prefect_aws import AwsClientParameters, AwsCredentials, S3Bucket


@pytest.fixture(scope="session")
def prefect():
    with prefect_test_harness():
        # setup credentials
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
        yield
