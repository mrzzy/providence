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

from anyio import Path
import pytest
from prefect.blocks.system import Secret
from prefect.testing.utilities import prefect_test_harness
from prefect_dbt import DbtCliProfile, TargetConfigs


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
        DbtCliProfile(
            name="providence",
            target="dev",
            target_configs=TargetConfigs(
                type="duckdb",
                schema="main",
                extras={
                    "extensions": ["httpfs", "parquet", "icu"],
                    "settings": {
                        "s3_region": "",
                        "s3_endpoint": "s3.us-west-004.backblazeb2.com",
                        "s3_access_key_id": os.environ["B2_ACCOUNT_ID"],
                        "s3_secret_access_key": os.environ["B2_APP_KEY"],
                    },
                },
            ),
        ).save("dbt-profile")
        # point dbt project folder
        os.environ["DBT_PROJECT_DIR"] = str(
            Path(__file__).parent.parent / "transforms" / "dbt"
        )

        yield
