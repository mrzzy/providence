#
# Providence
# Pipelines
# Deploy Pipelines to Prefect
#
# Usage: Expects the following environment variables to be set:
# - YNAB_BUDGET_ID: Id of the budget to retrieve from YNAB API.
# - PREFECT_WORK_POOL: Name of the work pool to execute tasks on.

import asyncio
import os
from pathlib import Path
from prefect import deploy
from prefect.deployments.runner import DeploymentImage
from simplygo import ingest_simplygo
from uob import ingest_uob
from ynab import ingest_ynab


async def deploy_pipelines():
    """Deploy pipelines to Prefect."""
    params = {
        "bucket": os.environ["PVD_LAKE_BUCKET"],
    }
    await deploy(
        await ingest_simplygo.to_deployment(
            name="pvd-ingest-simplygo",
            cron="@daily",
            parameters=params,
        ),
        await ingest_ynab.to_deployment(
            name="pvd-ingest-ynab",
            cron="@daily",
            parameters=params
            | {
                "budget_id": os.environ["YNAB_BUDGET_ID"],
            },
        ),
        await ingest_uob.to_deployment(
            name="pvd-ingest-uob",
            parameters=params,
        ),
        work_pool_name=os.environ["PREFECT_WORK_POOL"],
        image="ghcr.io/mrzzy/pvd-pipeline:latest",
        build=False,
    )


if __name__ == "__main__":
    asyncio.run(deploy_pipelines())
