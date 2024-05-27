#
# Providence
# Github Workflow Integration
# Integration Tests
#

import os
from prefect.testing.utilities import prefect_test_harness
from prefect_github import GitHubCredentials
import pytest

from execution.github import run_container, run_workflow


@pytest.mark.asyncio
async def test_github_run_container(prefect):
    await GitHubCredentials(token=os.environ["GITHUB_TOKEN"]).save(
        name="github-credentials",
        overwrite=True,
    )
    await run_container(
        image="ghcr.io/mrzzy/pvd-simplygo-src@sha256:171e4966196a20b1c8f9081791e042a98fb8958565943fc52d018b768b398f41",
        command="bash entrypoint.sh 2024-05-01"
    )
