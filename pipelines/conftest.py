#
# Providence
# SimplyGo Flow
# Pytest Fixtures

import os
from prefect.testing.utilities import prefect_test_harness
from prefect_github import GitHubCredentials
import pytest


@pytest.fixture(scope="session")
async def prefect():
    with prefect_test_harness():
        await GitHubCredentials(token=os.environ["GITHUB_TOKEN"]).save(
            name="github-credentials",
            overwrite=True,
        )
        yield
