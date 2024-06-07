#
# Providence
# Integration Tests
# Pytest Fixtures
#

# Usage: Set the following environment variables:
# - B2_ACCOUNT_ID: B2 account id.
# - B2_APP_KEY: B2 application key credentials.
# - SIMPLYGO_SRC_USERNAME: Username used to authenticate with SimplyGo.
# - SIMPLYGO_SRC_PASSWORD: Password used to authenticate with SimplyGo.
# - PVD_LAKE_BUCKET: Name of the B2 bucket to use as data lake.
# - YNAB_BUDGET_ID: Id of the budget to retrieve from YNAB API.

import os

import pytest
from prefect.blocks.system import Secret
from prefect.testing.utilities import prefect_test_harness


@pytest.fixture(scope="session")
def prefect():
    with prefect_test_harness():
        # setup credential blocks
        Secret(value=os.environ["B2_ACCOUNT_ID"]).save("b2-account-id", overwrite=True)
        Secret(value=os.environ["B2_APP_KEY"]).save("b2-app-key", overwrite=True)
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
